import asyncio
from unittest.mock import MagicMock

import pytest
import structlog

from src.api.dependencies import get_tenant_db
from src.core import scheduler, sentry, tenant_rls
from src.repositories import comandas_repository


class _SqliteSession:
    """Dependency-level session which deliberately does not enable PostgreSQL RLS."""

    bind = type("Bind", (), {"dialect": type("Dialect", (), {"name": "sqlite"})()})()


def test_tenant_dependency_binds_and_unbinds_tenant_log_context() -> None:
    async def run() -> None:
        structlog.contextvars.clear_contextvars()
        dependency = get_tenant_db(_SqliteSession(), {"tenant_id": 42})

        assert await dependency.__anext__() is not None
        assert structlog.contextvars.get_contextvars()["tenant_id"] == 42

        await dependency.aclose()
        assert "tenant_id" not in structlog.contextvars.get_contextvars()

    asyncio.run(run())


def test_rls_setup_failures_are_not_silenced() -> None:
    db = MagicMock()
    db.execute.side_effect = RuntimeError("RLS role unavailable")

    with pytest.raises(RuntimeError, match="RLS role unavailable"):
        tenant_rls.arm(db, 7)


def test_increment_version_is_scoped_to_tenant() -> None:
    db = MagicMock()
    db.execute.return_value.rowcount = 1

    assert comandas_repository.increment_version(db, 10, 3, 7) is True

    statement = str(db.execute.call_args.args[0])
    parameters = db.execute.call_args.args[1]
    assert "tenant_id = :tenant_id" in statement
    assert parameters["tenant_id"] == 7


def test_scheduler_failure_is_logged_and_sent_to_sentry(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[BaseException] = []
    monkeypatch.setattr(scheduler.sentry_sdk, "capture_exception", captured.append)
    exception = RuntimeError("job failed")
    event = MagicMock(job_id="cleanup", exception=exception, traceback=None)

    scheduler._log_job_outcome(event)

    assert captured == [exception]


def test_sentry_redacts_sensitive_breadcrumb_data() -> None:
    event = {"extra": {"token": "secret"}, "breadcrumbs": {"values": [{"cpf": "123"}]}}

    sanitized = sentry._redact_sentry_event(event, {})

    assert sanitized["extra"]["token"] == "[REDACTED]"
    assert sanitized["breadcrumbs"]["values"][0]["cpf"] == "[REDACTED]"
