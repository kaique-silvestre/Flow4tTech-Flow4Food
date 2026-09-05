from typing import Any, Callable, Optional, cast

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from src.core.logging import redact_sensitive_data


def _redact_sentry_event(event: dict[str, Any], _hint: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Apply the same credential/PII policy to Sentry extras and breadcrumbs."""
    return redact_sensitive_data(None, "before_send", event)


def init_sentry(dsn: str, env: str = "dev") -> None:
    """Initialize Sentry. No-op when DSN is empty (dev default)."""
    if not dsn:
        return
    sentry_sdk.init(
        dsn=dsn,
        environment=env,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1 if env == "prod" else 1.0,
        send_default_pii=False,
        before_send=cast(Callable[..., Any], _redact_sentry_event),
    )
