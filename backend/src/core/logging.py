from __future__ import annotations

import logging
import re
import sys
from collections.abc import Mapping
from typing import Any

import structlog

REDACTED_VALUE = "[REDACTED]"

# Keys are normalized before comparison so that common spelling variants such as
# ``accessToken``, ``access_token`` and ``Access-Token`` are all protected.
_SENSITIVE_KEY_PARTS = frozenset(
    {
        "senha",
        "password",
        "cpf",
        "token",
        "authorization",
        "secret",
        "apikey",
        "accesstoken",
        "refreshtoken",
        "bearertoken",
        "clientsecret",
    }
)


def _is_sensitive_key(key: object) -> bool:
    """Return whether a log-event key can contain credentials or PII."""
    if not isinstance(key, str):
        return False

    normalized = re.sub(r"[^a-z0-9]", "", key.lower())
    if normalized in _SENSITIVE_KEY_PARTS:
        return True

    # Covers delimiters and camelCase compound keys such as ``user_password``,
    # ``userPassword`` and ``authorizationHeader``. It is deliberately
    # conservative: redacting an extra field is preferable to leaking a secret.
    if any(
        part.lower() in _SENSITIVE_KEY_PARTS
        for part in re.split(r"[^a-zA-Z0-9]+", key)
        if part
    ):
        return True

    return any(normalized.startswith(part) or normalized.endswith(part) for part in _SENSITIVE_KEY_PARTS)


def _redact_sensitive_values(value: Any) -> Any:
    """Recursively redact sensitive fields in structured logging values."""
    if isinstance(value, Mapping):
        return {
            key: REDACTED_VALUE if _is_sensitive_key(key) else _redact_sensitive_values(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_sensitive_values(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_sensitive_values(item) for item in value)
    if isinstance(value, set):
        return {_redact_sensitive_values(item) for item in value}
    if isinstance(value, frozenset):
        return frozenset(_redact_sensitive_values(item) for item in value)
    return value


def redact_sensitive_data(
    _logger: Any, _method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Structlog processor that removes credentials and CPF before rendering."""
    return _redact_sensitive_values(event_dict)


def configure_logging(env: str = "dev", log_level: str = "INFO") -> None:
    """Configure structlog with JSON output and request_id context vars.

    ``log_level`` is read from the ``LOG_LEVEL`` env var by callers (see
    ``core/config.Settings.LOG_LEVEL``) so verbosity can be raised in staging/
    prod without a code change. Falls back to INFO for unknown values.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )
    # basicConfig() is a no-op for the stream/format setup once a handler is
    # already attached to the root logger (e.g. the first call in a process,
    # or a test harness that pre-installs its own handler) — but the level
    # must still take effect on every call, so set it explicitly.
    logging.root.setLevel(level)

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        redact_sensitive_data,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if env == "dev":
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "flow4food") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
