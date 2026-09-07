import contextvars
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.logging import get_logger

log = get_logger(__name__)


class _TenantContext:
    """Stores the current request's tenant_id for the duration of the request.

    Backed by contextvars.ContextVar (not threading.local): FastAPI/anyio may run
    a request's dependency setup, endpoint body, and dependency teardown on
    different threads drawn from a shared threadpool — threading.local state set
    by one request's setup could then leak into another concurrent request's
    checkout listener if both happen to land on the same worker OS thread.
    ContextVar is bound to the asyncio task (request) instead of the OS thread,
    and anyio's to_thread.run_sync() copies the *current* task context into each
    worker-thread call, so mutations made directly on the task (i.e. from an
    `async def` dependency, not one hopped through a threadpool call) are
    visible to every later threadpool call made within that same request.
    See get_tenant_db in api/dependencies.py — it must stay `async def` for
    this propagation to hold.

    Exposes the same `.tenant_id` attribute API the threading.local version
    had, so callers (the checkout listener below, get_tenant_db) don't change.
    """

    _var: "contextvars.ContextVar[Optional[int]]" = contextvars.ContextVar(
        "tenant_id", default=None
    )

    @property
    def tenant_id(self) -> Optional[int]:
        return self._var.get()

    @tenant_id.setter
    def tenant_id(self, value: Optional[int]) -> None:
        self._var.set(value)


# Read by the pool checkout listener (core/database.py) to re-establish RLS
# context on every connection checkout — including after db.commit() in
# SQLAlchemy 2.0 which releases the connection back to the pool.
_tenant_ctx = _TenantContext()


def _is_sqlite(db: Session) -> bool:
    return getattr(getattr(db.get_bind(), "dialect", None), "name", "") == "sqlite"


def arm(db: Session, tenant_id: int) -> None:
    """Switch the connection to the restricted app_user role scoped to tenant_id.

    No-op on SQLite — `SET ROLE` / `SET app.tenant_id` are Postgres-specific RLS
    syntax and error on SQLite, which the test suite uses by default.
    """
    if _is_sqlite(db):
        return
    db.execute(text("SET ROLE app_user"))
    db.execute(text("SET app.tenant_id = :tid"), {"tid": str(tenant_id)})
    _tenant_ctx.tenant_id = tenant_id
    log.info("tenant_rls_armed", tenant_id=tenant_id)


def clear(db: Session) -> None:
    """Clear RLS state before a connection is reused by another workload."""
    if _is_sqlite(db):
        return
    db.execute(text("RESET ROLE"))
    db.execute(text("SET app.tenant_id = ''"))
    _tenant_ctx.tenant_id = None
    log.info("tenant_rls_cleared")
