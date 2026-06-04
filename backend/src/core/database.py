from collections.abc import Generator
from contextvars import ContextVar
from typing import Optional

from sqlalchemy import create_engine, event, text
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

# Stores the current request's tenant_id in a thread-local context.
# Used by the after_begin listener to re-establish RLS context on every
# new transaction — necessary because SQLAlchemy 2.0 releases the
# connection back to the pool after each db.commit().
_tenant_id_var: ContextVar[Optional[int]] = ContextVar("_request_tenant_id", default=None)


@event.listens_for(Session, "after_begin")
def _auto_set_tenant_on_begin(session, transaction, connection):  # type: ignore[misc]
    """Re-establish RLS context at the start of every new transaction.

    SQLAlchemy 2.0 releases connections to the pool after each commit.
    The pool checkout listener resets ROLE and tenant_id on the fresh
    connection; this event re-sets them so every transaction within a
    request has the correct RLS context.
    """
    if getattr(transaction, "nested", False):
        return  # savepoint — connection already has correct context
    tid = _tenant_id_var.get()
    if tid is not None and connection.dialect.name == "postgresql":
        connection.execute(text("SET ROLE app_user"))
        connection.execute(text("SET app.tenant_id = :tid"), {"tid": str(tid)})


if _settings.DATABASE_URL.startswith("postgresql"):

    @event.listens_for(engine, "checkout")
    def _reset_tenant_on_checkout(dbapi_conn, connection_record, connection_proxy):
        cursor = dbapi_conn.cursor()
        cursor.execute("RESET ROLE")
        cursor.execute("SET app.tenant_id = ''")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
