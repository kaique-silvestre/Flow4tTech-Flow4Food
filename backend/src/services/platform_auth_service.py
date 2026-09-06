from datetime import timedelta

import bcrypt
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.repositories import platform_admins_repository
from src.services.auth_service import create_access_token

PLATFORM_TOKEN_EXPIRES = timedelta(hours=8)

# Hash de um segredo fixo (nunca usado como senha real), verificado quando o
# admin não existe/está inativo — mantém o custo de bcrypt constante para não
# deixar quem tenta enumerar emails distinguir "não existe" (resposta rápida,
# sem bcrypt) de "existe, senha errada" (resposta lenta, com bcrypt) pelo tempo
# de resposta.
_DUMMY_PASSWORD_HASH = bcrypt.hashpw(b"dummy-password-for-timing", bcrypt.gensalt()).decode()


def create_platform_token(platform_admin_id: int, email: str) -> str:
    payload = {
        "sub": str(platform_admin_id),
        "platform_admin_id": platform_admin_id,
        "platform_admin": True,
        "email": email,
    }
    return create_access_token(payload, expires_delta=PLATFORM_TOKEN_EXPIRES)


def login(db: Session, email: str, password: str) -> str:
    admin = platform_admins_repository.get_by_email(db, email)
    if admin is None or not admin.is_active:
        # Always pay the bcrypt cost, even for an admin that doesn't exist (or
        # is inactive) — otherwise a nonexistent email returns almost
        # instantly while a wrong password for a real email takes as long as
        # bcrypt does, letting an attacker enumerate valid emails by timing.
        bcrypt.checkpw(password.encode(), _DUMMY_PASSWORD_HASH.encode())
        raise AppError(code=ErrorCode.SENHA_INCORRETA, message="Email ou senha inválidos", http_status=401)
    if not bcrypt.checkpw(password.encode(), admin.password_hash.encode()):
        raise AppError(code=ErrorCode.SENHA_INCORRETA, message="Email ou senha inválidos", http_status=401)
    return create_platform_token(admin.id, admin.email)
