import hashlib
import secrets
import smtplib
import uuid
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import bcrypt
import jwt
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.errors import AppError, ErrorCode
from src.core.logging import get_logger
from src.models.system_users import PasswordReset
from src.repositories import refresh_tokens_repository
from src.repositories.password_reset_repository import (
    create_reset,
    get_reset_by_token,
    get_valid_reset,
    invalidate_user_resets,
)
from src.repositories.users_repository import (
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
)
from src.schemas.auth import GenericMessage, ResetTokenInfo, TokenResponse, UserInfo

log = get_logger(__name__)

_DEFAULT_TENANT_ID = 1  # TODO(Issue 3): resolve from onboarding/subdomain
_INVALID_MSG = "Email/usuário ou senha inválidos"


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(payload: dict) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRES_HOURS)
    return jwt.encode(
        {**payload, "jti": str(uuid.uuid4()), "exp": expire},
        settings.JWT_SECRET,
        algorithm="HS256",
    )


def _build_token_response(user) -> TokenResponse:
    permissions = [p.screen for p in user.profile.permissions if p.can_access]
    payload = {
        "sub": str(user.id),
        "user_id": user.id,
        "tenant_id": user.tenant_id,
        "username": user.username,
        "name": user.name,
        "profile_id": user.profile_id,
        "profile_name": user.profile.name,
        "permissions": permissions,
    }
    return TokenResponse(access_token=create_access_token(payload))


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def create_refresh_token(db: Session, user_id: int) -> str:
    settings = get_settings()
    raw = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS)
    refresh_tokens_repository.create(db, user_id, token_hash, expires_at)
    return raw


def rotate_refresh_token(db: Session, raw_token: str) -> tuple[str, str]:
    token_hash = _hash_token(raw_token)
    record = refresh_tokens_repository.get_by_hash(db, token_hash)
    if record is None or record.revoked_at is not None:
        raise AppError(code=ErrorCode.VALIDATION_ERROR, message="Refresh token inválido", http_status=401)
    if record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise AppError(code=ErrorCode.VALIDATION_ERROR, message="Refresh token expirado", http_status=401)
    refresh_tokens_repository.revoke(db, record.id)
    user = get_user_by_id(db, record.user_id)
    if user is None or not user.is_active:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Usuário não encontrado", http_status=401)
    permissions = [p.screen for p in user.profile.permissions if p.can_access]
    payload = {
        "sub": str(user.id),
        "user_id": user.id,
        "tenant_id": user.tenant_id,
        "username": user.username,
        "name": user.name,
        "profile_id": user.profile_id,
        "profile_name": user.profile.name,
        "permissions": permissions,
    }
    new_access = create_access_token(payload)
    new_refresh = create_refresh_token(db, user.id)
    return new_access, new_refresh


def revoke_all_refresh_tokens(db: Session, user_id: int) -> None:
    refresh_tokens_repository.revoke_all_for_user(db, user_id)


def login(db: Session, identifier: str, password: str) -> TokenResponse:
    if "@" in identifier:
        user = get_user_by_email(db, identifier)
    else:
        user = get_user_by_username(db, _DEFAULT_TENANT_ID, identifier)

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
        name=payload.get("name") or payload.get("username", ""),
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


def _send_reset_email(to_email: str, name: str, reset_url: str) -> None:
    settings = get_settings()
    if not settings.SMTP_HOST:
        log.info("reset_link_no_smtp", email=to_email, url=reset_url)
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Redefinição de senha — Flow4Tech"
        msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
        msg["To"] = to_email
        body = (
            f"Olá, {name}!\n\n"
            f"Clique no link abaixo para redefinir sua senha no Flow4Food (válido por 1 hora):\n\n"
            f"{reset_url}\n\n"
            f"Se você não solicitou a redefinição, ignore este email.\n\n"
            f"Flow4Food — por Flow4Tech\n"
        )
        msg.attach(MIMEText(body, "plain", "utf-8"))
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(msg["From"], [to_email], msg.as_string())
    except Exception as exc:
        log.error("reset_email_failed", email=to_email, error=str(exc))


def forgot_password(db: Session, email: str) -> GenericMessage:
    _SUCCESS = "Se o email estiver cadastrado, você receberá um link de redefinição em instantes."
    user = get_user_by_email(db, email)
    if user is None or not user.is_active:
        return GenericMessage(message=_SUCCESS)

    invalidate_user_resets(db, user.id)
    token = str(uuid.uuid4())
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
    create_reset(db, PasswordReset(user_id=user.id, token=token, expires_at=expires))

    settings = get_settings()
    reset_url = f"{settings.FRONTEND_URL}/redefinir-senha?token={token}"
    _send_reset_email(user.email or "", user.name, reset_url)
    return GenericMessage(message=_SUCCESS)


def get_reset_token_info(db: Session, token: str) -> ResetTokenInfo:
    reset = get_valid_reset(db, token)
    if reset is None:
        existing = get_reset_by_token(db, token)
        if existing and existing.used_at:
            raise AppError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Link já utilizado. Solicite um novo se precisar.",
                http_status=400,
            )
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Link expirado. Solicite um novo.",
            http_status=400,
        )
    return ResetTokenInfo(name=reset.user.name)


def reset_password(db: Session, token: str, new_password: str) -> None:
    if len(new_password) < 6:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Nova senha deve ter no mínimo 6 caracteres",
            http_status=400,
        )
    reset = get_valid_reset(db, token)
    if reset is None:
        existing = get_reset_by_token(db, token)
        if existing and existing.used_at:
            raise AppError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Link já utilizado. Solicite um novo se precisar.",
                http_status=400,
            )
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Link expirado. Solicite um novo.",
            http_status=400,
        )
    user = get_user_by_id(db, reset.user_id)
    if user is None:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Usuário não encontrado", http_status=404)
    user.password_hash = hash_password(new_password)
    reset.used_at = datetime.now(timezone.utc)
    db.commit()


# kept for backward compat — old single-password flow no longer used
def authenticate(db: Session, senha: str) -> str:
    raise AppError(code=ErrorCode.SENHA_INCORRETA, message="Use o novo endpoint de login", http_status=410)
