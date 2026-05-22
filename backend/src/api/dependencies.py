from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.core.config import get_settings
from src.core.database import get_db

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_bearer)],
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente")
    settings = get_settings()
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
        ) from exc


def require_permission(screen: str):
    """FastAPI dependency factory — verifica se usuário tem permissão para a tela."""

    def _check(payload: dict = Depends(get_current_user)) -> dict:
        permissions: list[str] = payload.get("permissions", [])
        # tokens legados (sub=estabelecimento) não têm permissions[] — conceder acesso temporário
        if "user_id" in payload and screen not in permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Sem permissão: {screen}")
        return payload

    return _check


__all__ = ["get_db", "get_current_user", "require_permission"]
