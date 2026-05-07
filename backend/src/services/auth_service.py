from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.errors import AppError, ErrorCode
from src.repositories.auth_repository import get_config, upsert_config


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRES_HOURS)
    payload = {**data, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def authenticate(db: Session, senha: str) -> str:
    config = get_config(db)
    if config is None:
        upsert_config(db, hash_password(senha))
    else:
        if not verify_password(senha, config.senha_hash):
            raise AppError(
                code=ErrorCode.SENHA_INCORRETA,
                message="Senha incorreta",
                http_status=401,
            )
    return create_access_token({"sub": "estabelecimento"})
