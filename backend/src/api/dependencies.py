from collections.abc import Generator
from typing import Annotated, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.database import _tenant_id_var, engine, get_db
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

    Sets _tenant_id_var in the current thread context so the
    Session.after_begin event listener re-establishes RLS context at
    the start of every new transaction — including after db.commit(),
    which in SQLAlchemy 2.0 releases and re-checks-out the connection.
    The pool checkout listener handles cleanup on connection return.
    """
    tenant_id = payload.get("tenant_id")
    token = None
    if tenant_id is not None and engine.dialect.name == "postgresql":
        token = _tenant_id_var.set(tenant_id)
    try:
        yield db
    finally:
        if token is not None:
            _tenant_id_var.reset(token)


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
