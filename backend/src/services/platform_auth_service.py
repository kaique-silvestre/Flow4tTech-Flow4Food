import bcrypt
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.repositories import platform_admins_repository
from src.services.auth_service import create_access_token


def create_platform_token(platform_admin_id: int, email: str) -> str:
    payload = {
        "sub": str(platform_admin_id),
        "platform_admin_id": platform_admin_id,
        "platform_admin": True,
        "email": email,
    }
    return create_access_token(payload)


def login(db: Session, email: str, password: str) -> str:
    admin = platform_admins_repository.get_by_email(db, email)
    if admin is None or not admin.is_active:
        raise AppError(code=ErrorCode.SENHA_INCORRETA, message="Email ou senha inválidos", http_status=401)
    if not bcrypt.checkpw(password.encode(), admin.password_hash.encode()):
        raise AppError(code=ErrorCode.SENHA_INCORRETA, message="Email ou senha inválidos", http_status=401)
    return create_platform_token(admin.id, admin.email)
