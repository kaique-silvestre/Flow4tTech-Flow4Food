import contextvars
from collections.abc import Generator
from typing import Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.core.config import get_settings
from src.core.logging import get_logger


class Base(DeclarativeBase):
    pass


_settings = get_settings()
log = get_logger(__name__)


def _engine_options(url: str) -> dict:
    """Return explicit production-pool settings without breaking SQLite tests."""
    options: dict = {"pool_pre_ping": True, "future": True}
    if url.startswith("postgresql"):
        options.update(
            connect_args={"options": "-c timezone=UTC"},
            pool_size=_settings.DB_POOL_SIZE,
            max_overflow=_settings.DB_MAX_OVERFLOW,
            pool_timeout=_settings.DB_POOL_TIMEOUT,
        )
    return options


engine = create_engine(_settings.DATABASE_URL, **_engine_options(_settings.DATABASE_URL))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


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


# Read by the pool checkout listener to re-establish RLS context on every
# connection checkout — including after db.commit() in SQLAlchemy 2.0
# which releases the connection back to the pool.
_tenant_ctx = _TenantContext()


if _settings.DATABASE_URL.startswith("postgresql"):

    @event.listens_for(engine, "checkout")
    def _configure_tenant_on_checkout(dbapi_conn, connection_record, connection_proxy):
        """Reset tenant context on checkout, then re-establish if a request is active.

        Fires on every pool checkout — including after db.commit() in SQLAlchemy 2.0
        which releases and re-checks-out the connection for the next transaction.
        Using raw DBAPI cursor avoids any SQLAlchemy ORM event recursion issues.
        """
        cursor = dbapi_conn.cursor()
        cursor.execute("RESET ROLE")
        cursor.execute("SET app.tenant_id = ''")
        tid = getattr(_tenant_ctx, "tenant_id", None)
        if tid is not None:
            cursor.execute("SET ROLE app_user")
            cursor.execute(f"SET app.tenant_id = '{int(tid)}'")
        cursor.close()


def _is_sqlite(db: Session) -> bool:
    return getattr(getattr(db.get_bind(), "dialect", None), "name", "") == "sqlite"


def set_tenant_context(db: Session, tenant_id: int) -> None:
    """Set the tenant variable and leave an auditable structured trace.

    No-op on SQLite — `SET app.tenant_id` is Postgres-specific RLS syntax and
    errors on SQLite, which the test suite uses by default.
    """
    if _is_sqlite(db):
        return
    db.execute(text("SET app.tenant_id = :tid"), {"tid": str(tenant_id)})
    log.info("tenant_context_set", tenant_id=tenant_id)


def set_tenant_rls_context(db: Session, tenant_id: int) -> None:
    """Apply the restricted application role and tenant RLS context."""
    if _is_sqlite(db):
        return
    db.execute(text("SET ROLE app_user"))
    set_tenant_context(db, tenant_id)


def clear_tenant_rls_context(db: Session) -> None:
    """Clear RLS state before a connection is reused by another workload."""
    if _is_sqlite(db):
        return
    db.execute(text("RESET ROLE"))
    db.execute(text("SET app.tenant_id = ''"))
    log.info("tenant_rls_context_cleared")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Platform engine — separate pool, no RLS, no tenant context listener.
# DATABASE_URL_PLATFORM must be set explicitly: it is expected to point at a
# connection/role isolated from the tenant-scoped DATABASE_URL, so silently
# falling back would let platform-admin traffic run on the same role as
# regular tenant traffic.
if not _settings.DATABASE_URL_PLATFORM:
    raise RuntimeError(
        "DATABASE_URL_PLATFORM is not set. Set it explicitly to an isolated "
        "connection string for the platform engine — it must not fall back "
        "to DATABASE_URL."
    )
_platform_url = _settings.DATABASE_URL_PLATFORM
platform_engine = create_engine(_platform_url, **_engine_options(_platform_url))
PlatformSessionLocal = sessionmaker(bind=platform_engine, autoflush=False, autocommit=False, future=True)

# Scheduled jobs use their own bounded pool so slow maintenance work cannot
# exhaust connections reserved for HTTP traffic.
scheduler_engine = create_engine(_settings.DATABASE_URL, **_engine_options(_settings.DATABASE_URL))
SchedulerSessionLocal = sessionmaker(bind=scheduler_engine, autoflush=False, autocommit=False, future=True)


def get_platform_db() -> Generator[Session, None, None]:
    db = PlatformSessionLocal()
    try:
        yield db
    finally:
        db.close()
