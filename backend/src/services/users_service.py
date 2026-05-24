import secrets
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.system_users import SystemUser
from src.repositories.profiles_repository import get_admin_profile, get_profile_by_id
from src.repositories.users_repository import (
    count_active_admins,
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    list_users,
    update_user,
)
from src.schemas.users import UserCreate, UserResponse, UserUpdate
from src.services.auth_service import hash_password

TENANT_ID = 1


def _to_response(user: SystemUser) -> UserResponse:
    return UserResponse(
        id=user.id,
        tenant_id=user.tenant_id,
        profile_id=user.profile_id,
        profile_name=user.profile.name,
        name=user.name,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
    )


def get_users(db: Session, search: Optional[str] = None, profile_id: Optional[int] = None) -> list[UserResponse]:
    users = list_users(db, TENANT_ID, search, profile_id)
    return [_to_response(u) for u in users]


def get_user(db: Session, user_id: int) -> UserResponse:
    user = get_user_by_id(db, user_id)
    if not user or user.tenant_id != TENANT_ID:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Usuário não encontrado", http_status=404)
    return _to_response(user)


def create_new_user(db: Session, data: UserCreate) -> UserResponse:
    if get_user_by_username(db, TENANT_ID, data.username):
        raise AppError(code=ErrorCode.CONFLICT, message="Username já em uso", field="username", http_status=409)
    if data.email and get_user_by_email(db, data.email):
        raise AppError(code=ErrorCode.CONFLICT, message="Email já em uso", field="email", http_status=409)
    profile = get_profile_by_id(db, data.profile_id)
    if not profile or profile.tenant_id != TENANT_ID:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Perfil não encontrado", http_status=404)

    user = SystemUser(
        tenant_id=TENANT_ID,
        profile_id=data.profile_id,
        name=data.name,
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        is_active=data.is_active,
    )
    return _to_response(create_user(db, user))


def update_existing_user(db: Session, user_id: int, data: UserUpdate, current_user_id: int) -> UserResponse:
    user = get_user_by_id(db, user_id)
    if not user or user.tenant_id != TENANT_ID:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Usuário não encontrado", http_status=404)
    if user_id == current_user_id and data.profile_id is not None:
        raise AppError(code=ErrorCode.CONFLICT, message="Não pode alterar o próprio perfil", http_status=409)

    if data.email is not None and data.email != user.email:
        existing = get_user_by_email(db, data.email)
        if existing and existing.id != user_id:
            raise AppError(code=ErrorCode.CONFLICT, message="Email já em uso", field="email", http_status=409)

    if data.name is not None:
        user.name = data.name
    if data.email is not None:
        user.email = data.email
    if data.profile_id is not None:
        profile = get_profile_by_id(db, data.profile_id)
        if not profile or profile.tenant_id != TENANT_ID:
            raise AppError(code=ErrorCode.NOT_FOUND, message="Perfil não encontrado", http_status=404)
        user.profile_id = data.profile_id
    if data.is_active is not None:
        if not data.is_active:
            _check_not_last_admin(db, user)
        user.is_active = data.is_active

    user.updated_at = datetime.now(timezone.utc)
    return _to_response(update_user(db, user))


def toggle_user_active(db: Session, user_id: int, current_user_id: int) -> UserResponse:
    if user_id == current_user_id:
        raise AppError(code=ErrorCode.CONFLICT, message="Não pode desativar a si mesmo", http_status=409)
    user = get_user_by_id(db, user_id)
    if not user or user.tenant_id != TENANT_ID:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Usuário não encontrado", http_status=404)
    if user.is_active:
        _check_not_last_admin(db, user)
        user.is_active = False
    else:
        user.is_active = True
    user.updated_at = datetime.now(timezone.utc)
    return _to_response(update_user(db, user))


def delete_existing_user(db: Session, user_id: int, current_user_id: int) -> None:
    if user_id == current_user_id:
        raise AppError(code=ErrorCode.CONFLICT, message="Não pode excluir a si mesmo", http_status=409)
    user = get_user_by_id(db, user_id)
    if not user or user.tenant_id != TENANT_ID:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Usuário não encontrado", http_status=404)
    _check_not_last_admin(db, user)
    delete_user(db, user)


def reset_password(db: Session, user_id: int) -> str:
    user = get_user_by_id(db, user_id)
    if not user or user.tenant_id != TENANT_ID:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Usuário não encontrado", http_status=404)
    # Remove ambiguous chars: 0/O, l/1/I, etc.
    alphabet = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789"
    temp = "".join(secrets.choice(alphabet) for _ in range(10))
    user.password_hash = hash_password(temp)
    user.updated_at = datetime.now(timezone.utc)
    update_user(db, user)
    return temp


def check_username_available(db: Session, username: str) -> bool:
    return get_user_by_username(db, TENANT_ID, username) is None


def check_email_available(db: Session, email: str) -> bool:
    return get_user_by_email(db, email) is None


def _check_not_last_admin(db: Session, user: SystemUser) -> None:
    admin_profile = get_admin_profile(db, TENANT_ID)
    if admin_profile and user.profile_id == admin_profile.id:
        active_count = count_active_admins(db, TENANT_ID, admin_profile.id)
        if active_count <= 1:
            raise AppError(
                code=ErrorCode.CONFLICT,
                message="Não é possível remover o último Admin ativo",
                http_status=409,
            )
