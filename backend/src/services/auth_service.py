from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.errors import AppError, ErrorCode
from src.repositories.users_repository import (
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
)
from src.schemas.auth import TokenResponse, UserInfo

TENANT_ID = 1
_INVALID_MSG = "Email/usuário ou senha inválidos"


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(payload: dict) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(hours=8)
    return jwt.encode({**payload, "exp": expire}, settings.JWT_SECRET, algorithm="HS256")


def _build_token_response(user) -> TokenResponse:
    permissions = [p.screen for p in user.profile.permissions if p.can_access]
    payload = {
        "sub": str(user.id),
        "user_id": user.id,
        "tenant_id": user.tenant_id,
        "username": user.username,
        "profile_id": user.profile_id,
        "profile_name": user.profile.name,
        "permissions": permissions,
    }
    return TokenResponse(access_token=create_access_token(payload))


def login(db: Session, identifier: str, password: str) -> TokenResponse:
    if "@" in identifier:
        user = get_user_by_email(db, identifier)
    else:
        user = get_user_by_username(db, TENANT_ID, identifier)

    if user is None or not user.is_active:
        raise AppError(code=ErrorCode.SENHA_INCORRETA, message=_INVALID_MSG, http_status=401)

    if not verify_password(password, user.password_hash):
        raise AppError(code=ErrorCode.SENHA_INCORRETA, message=_INVALID_MSG, http_status=401)

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    return _build_token_response(user)


def get_current_user_info(payload: dict) -> UserInfo:
    return UserInfo(
        user_id=payload["user_id"],
        tenant_id=payload["tenant_id"],
        username=payload["username"],
        name=payload.get("username", ""),
        profile_id=payload["profile_id"],
        profile_name=payload["profile_name"],
        permissions=payload.get("permissions", []),
    )


def change_password(db: Session, user_id: int, current_password: str, new_password: str) -> None:
    if len(new_password) < 6:
        raise AppError(code=ErrorCode.VALIDATION_ERROR, message="Nova senha deve ter no mínimo 6 caracteres", http_status=400)
    user = get_user_by_id(db, user_id)
    if user is None:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Usuário não encontrado", http_status=404)
    if not verify_password(current_password, user.password_hash):
        raise AppError(code=ErrorCode.SENHA_INCORRETA, message="Senha atual incorreta", http_status=401)
    user.password_hash = hash_password(new_password)
    db.commit()


# kept for backward compat — old single-password flow no longer used
def authenticate(db: Session, senha: str) -> str:
    raise AppError(code=ErrorCode.SENHA_INCORRETA, message="Use o novo endpoint de login", http_status=410)
