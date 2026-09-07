from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.core.config import get_settings
from src.core.logging import get_logger
from src.core.tenant_rls import _tenant_ctx


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
