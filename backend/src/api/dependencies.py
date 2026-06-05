from collections.abc import Generator
from typing import Annotated, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.database import _tenant_ctx, get_db
from src.repositories import revoked_tokens_repository

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_bearer)],
    db: Session = Depends(get_db),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente")
    settings = get_settings()
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"])
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
        ) from exc
    jti = payload.get("jti")
    if jti and revoked_tokens_repository.is_revoked(db, jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revogado")
    return payload


def get_tenant_db(
    db: Session = Depends(get_db),
    payload: dict = Depends(get_current_user),
) -> Generator[Session, None, None]:
    """Session scoped to tenant via RLS (PostgreSQL only).

    Two-layer approach:
    1. Direct SET on db session here — necessary because get_current_user runs
       is_revoked() (a SQL query) before this function, which checks out the
       connection from the pool BEFORE _tenant_ctx is set. The checkout listener
       fires without tenant context. We must re-apply SET ROLE / SET tenant_id
       explicitly on the already-checked-out connection.
    2. _tenant_ctx (thread-local) is set so the pool checkout listener
       re-establishes RLS context on any NEW connection checked out after
       db.commit() (SQLAlchemy 2.0 releases connection on commit).
    """
    tenant_id = payload.get("tenant_id")
    # Use session's bound engine — not the module-level engine — to detect dialect.
    # In unit tests, db may be bound to SQLite while DATABASE_URL / engine is PostgreSQL.
    _bind = getattr(db, "bind", None)
    _dialect = getattr(getattr(_bind, "dialect", None), "name", "")
    is_pg = tenant_id is not None and _dialect == "postgresql"
    if is_pg:
        _tenant_ctx.tenant_id = tenant_id
        db.execute(text("SET ROLE app_user"))
        db.execute(text("SET app.tenant_id = :tid"), {"tid": str(tenant_id)})
    try:
        yield db
    finally:
        if is_pg:
            _tenant_ctx.tenant_id = None


def require_permission(screen: str):
    def _check(payload: dict = Depends(get_current_user)) -> dict:
        if "user_id" not in payload:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token sem user_id")
        permissions: list[str] = payload.get("permissions", [])
        if screen not in permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Sem permissão: {screen}")
        return payload

    return _check


def require_active_subscription(payload: dict = Depends(get_current_user)) -> dict:
    sub_status = payload.get("subscription_status", "trial")
    if sub_status not in {"ativa", "trial"}:
        raise HTTPException(status_code=402, detail="Assinatura vencida ou suspensa")
    return payload


__all__ = ["get_db", "get_tenant_db", "get_current_user", "require_permission", "require_active_subscription"]
