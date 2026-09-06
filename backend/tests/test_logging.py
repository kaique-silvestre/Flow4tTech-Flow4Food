import logging

import pytest
import structlog

from src.core.logging import configure_logging, redact_sensitive_data


@pytest.fixture(autouse=True)
def _reset_structlog() -> None:
    structlog.reset_defaults()
    structlog.contextvars.clear_contextvars()
    yield
    structlog.contextvars.clear_contextvars()
    structlog.reset_defaults()


def test_redact_sensitive_data_preserves_safe_values_and_recurses() -> None:
    event_dict = {
        "event": "login_attempt",
        "user_id": 42,
        "Password": "plain-password",
        "customer": {
            "cpf": "123.456.789-00",
            "name": "Ana",
            "userPassword": "nested-password",
        },
        "credentials": [
            {"access_token": "access-secret"},
            ("safe-value", {"api_key": "api-secret"}),
        ],
    }

    result = redact_sensitive_data(None, "info", event_dict)

    assert result["event"] == "login_attempt"
    assert result["user_id"] == 42
    assert result["Password"] == "[REDACTED]"
    assert result["customer"] == {
        "cpf": "[REDACTED]",
        "name": "Ana",
        "userPassword": "[REDACTED]",
    }
    assert result["credentials"] == [
        {"access_token": "[REDACTED]"},
        ("safe-value", {"api_key": "[REDACTED]"}),
    ]


@pytest.mark.parametrize("env", ["dev", "production"])
def test_configured_renderers_do_not_expose_sensitive_event_or_bound_context(
    caplog: pytest.LogCaptureFixture, env: str
) -> None:
    configure_logging(env)
    caplog.set_level(logging.INFO)
    structlog.contextvars.bind_contextvars(refresh_token="bound-secret")

    structlog.get_logger("test.logging").info(
        "login_attempt",
        senha="event-password",
        authorization="Bearer event-token",
        request_id="safe-request-id",
    )

    rendered = caplog.text
    for secret in ("bound-secret", "event-password", "event-token"):
        assert secret not in rendered
    assert "[REDACTED]" in rendered
    assert "login_attempt" in rendered
    assert "safe-request-id" in rendered


@pytest.mark.parametrize(
    "log_level, expected",
    [("DEBUG", logging.DEBUG), ("WARNING", logging.WARNING), ("info", logging.INFO)],
)
def test_configure_logging_applies_log_level_argument(log_level: str, expected: int) -> None:
    configure_logging("dev", log_level=log_level)

    assert logging.root.level == expected


def test_configure_logging_defaults_to_info_level() -> None:
    configure_logging("dev")

    assert logging.root.level == logging.INFO
