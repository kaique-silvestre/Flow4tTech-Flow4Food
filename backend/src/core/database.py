import threading
from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.core.config import get_settings


class Base(DeclarativeBase):
    pass


_settings = get_settings()
engine = create_engine(
    _settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True,
    connect_args={"options": "-c timezone=UTC"},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Stores the current request's tenant_id for the duration of the request.
# Uses threading.local (not ContextVar) because FastAPI runs sync routes in
# threadpool threads and generator cleanup may run in a different asyncio
# context — thread-local is correct for threadpool-scoped state.
# Read by the pool checkout listener to re-establish RLS context on every
# connection checkout — including after db.commit() in SQLAlchemy 2.0
# which releases the connection back to the pool.
_tenant_ctx = threading.local()


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
# Falls back to DATABASE_URL when DATABASE_URL_PLATFORM is empty (dev only).
_platform_url = _settings.DATABASE_URL_PLATFORM or _settings.DATABASE_URL
_platform_connect_args: dict = {}
if _platform_url.startswith("postgresql"):
    _platform_connect_args = {"options": "-c timezone=UTC"}
platform_engine = create_engine(
    _platform_url,
    pool_pre_ping=True,
    future=True,
    connect_args=_platform_connect_args,
)
PlatformSessionLocal = sessionmaker(bind=platform_engine, autoflush=False, autocommit=False, future=True)


def get_platform_db() -> Generator[Session, None, None]:
    db = PlatformSessionLocal()
    try:
        yield db
    finally:
        db.close()
