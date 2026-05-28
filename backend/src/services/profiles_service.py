from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.profiles import Profile
from src.repositories.profiles_repository import (
    delete_profile,
    get_profile_by_id,
    list_profiles,
    update_profile,
)
from src.schemas.profiles import ProfileCreate, ProfileResponse, ProfileUpdate


def _to_response(profile: Profile, user_count: int = 0) -> ProfileResponse:
    return ProfileResponse(
        id=profile.id,
        tenant_id=profile.tenant_id,
        name=profile.name,
        description=profile.description,
        is_system=profile.is_system,
        is_active=profile.is_active,
        permissions=[p.screen for p in profile.permissions if p.can_access],
        user_count=user_count,
        created_at=profile.created_at,
    )


def get_profiles(db: Session, tenant_id: int) -> list[ProfileResponse]:
    rows = list_profiles(db, tenant_id)
    return [_to_response(profile, count) for profile, count in rows]


def get_profile(db: Session, tenant_id: int, profile_id: int) -> ProfileResponse:
    profile = get_profile_by_id(db, profile_id)
    if not profile or profile.tenant_id != tenant_id:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Perfil não encontrado", http_status=404)
    rows = list_profiles(db, tenant_id)
    count = next((c for p, c in rows if p.id == profile_id), 0)
    return _to_response(profile, count)


def create_new_profile(db: Session, tenant_id: int, data: ProfileCreate) -> ProfileResponse:
    profile = Profile(
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        is_system=False,
    )
    db.add(profile)
    db.flush()
    return _to_response(update_profile(db, profile, data.screens))


def update_existing_profile(
    db: Session, tenant_id: int, profile_id: int, data: ProfileUpdate
) -> ProfileResponse:
    profile = get_profile_by_id(db, profile_id)
    if not profile or profile.tenant_id != tenant_id:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Perfil não encontrado", http_status=404)
    if profile.name == "Admin":
        raise AppError(code=ErrorCode.CONFLICT, message="Permissões do Admin não podem ser alteradas", http_status=409)

    if data.name is not None:
        profile.name = data.name
    if data.description is not None:
        profile.description = data.description
    profile.updated_at = datetime.now(timezone.utc)

    screens: Optional[list[str]] = None
    if data.screens is not None:
        screens = data.screens
    else:
        screens = [p.screen for p in profile.permissions if p.can_access]

    return _to_response(update_profile(db, profile, screens))


def toggle_profile_active(db: Session, tenant_id: int, profile_id: int) -> ProfileResponse:
    profile = get_profile_by_id(db, profile_id)
    if not profile or profile.tenant_id != tenant_id:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Perfil não encontrado", http_status=404)
    if profile.name == "Admin":
        raise AppError(code=ErrorCode.CONFLICT, message="O perfil Admin não pode ser desativado", http_status=409)
    if profile.users:
        raise AppError(code=ErrorCode.CONFLICT, message="Perfil possui usuários vinculados e não pode ser desativado", http_status=409)
    profile.is_active = not profile.is_active
    profile.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)
    rows = list_profiles(db, tenant_id)
    count = next((c for p, c in rows if p.id == profile_id), 0)
    return _to_response(profile, count)


def delete_existing_profile(db: Session, tenant_id: int, profile_id: int) -> None:
    profile = get_profile_by_id(db, profile_id)
    if not profile or profile.tenant_id != tenant_id:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Perfil não encontrado", http_status=404)
    if profile.is_system:
        raise AppError(code=ErrorCode.CONFLICT, message="Perfis de sistema não podem ser excluídos", http_status=409)
    if profile.users:
        user_names = [u.name for u in profile.users]
        raise AppError(
            code=ErrorCode.CONFLICT,
            message=f"Perfil possui usuários vinculados: {', '.join(user_names)}",
            http_status=409,
        )
    delete_profile(db, profile)
