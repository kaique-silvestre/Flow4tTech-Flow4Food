from typing import Annotated, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.database import get_db
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


def require_permission(screen: str):
    def _check(payload: dict = Depends(get_current_user)) -> dict:
        if "user_id" not in payload:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token sem user_id")
        permissions: list[str] = payload.get("permissions", [])
        if screen not in permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Sem permissão: {screen}")
        return payload

    return _check


__all__ = ["get_db", "get_current_user", "require_permission"]
