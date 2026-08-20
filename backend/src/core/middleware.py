import re
import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.core.logging import get_logger

log = get_logger(__name__)

# Accepts only safe, UUID-like request IDs (alphanumeric + hyphens, capped length).
# Anything else is discarded and a fresh server-side id is generated instead,
# preventing log injection / forged correlation ids from client-supplied headers.
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{1,64}$")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Adds request_id to structlog context vars and response header."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        client_request_id = request.headers.get("X-Request-ID")
        if client_request_id and _REQUEST_ID_PATTERN.match(client_request_id):
            request_id = client_request_id
        else:
            request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            log.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                latency_ms=elapsed_ms,
            )

        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Sets baseline security response headers on every response.

    This is a pure JSON API (the only HTML-ish surface, /docs, is already
    disabled outside non-prod envs), so a strict CSP is safe here. HSTS is
    only sent in prod: Railway terminates TLS in front of the app, so prod
    traffic is always HTTPS, but dev/staging/test may be plain HTTP and
    sending HSTS there could force browsers to refuse http:// for a year.
    """

    def __init__(self, app, env: str) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._send_hsts = env == "prod"

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'none'"
        if self._send_hsts:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response
