from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from src.models.profiles import Profile, ProfilePermission
from src.models.system_users import SystemUser


def _with_permissions(q):
    return q.options(joinedload(Profile.permissions))


def get_admin_profile(db: Session, tenant_id: int) -> Optional[Profile]:
    return (
        db.query(Profile)
        .filter(Profile.tenant_id == tenant_id, Profile.name == "Admin")
        .first()
    )


def get_profile_by_id(db: Session, profile_id: int) -> Optional[Profile]:
    return _with_permissions(
        db.query(Profile).filter(Profile.id == profile_id)
    ).first()


def list_profiles(db: Session, tenant_id: int) -> list[tuple[Profile, int]]:
    user_counts = (
        db.query(SystemUser.profile_id, func.count(SystemUser.id).label("cnt"))
        .filter(SystemUser.tenant_id == tenant_id)
        .group_by(SystemUser.profile_id)
        .subquery()
    )
    rows = (
        _with_permissions(db.query(Profile, func.coalesce(user_counts.c.cnt, 0)))
        .outerjoin(user_counts, Profile.id == user_counts.c.profile_id)
        .filter(Profile.tenant_id == tenant_id)
        .order_by(Profile.name)
        .all()
    )
    return rows


def create_profile(db: Session, profile: Profile) -> Profile:
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return get_profile_by_id(db, profile.id)  # type: ignore[return-value]


def update_profile(db: Session, profile: Profile, screens: list[str]) -> Profile:
    db.query(ProfilePermission).filter(ProfilePermission.profile_id == profile.id).delete()
    for screen in screens:
        db.add(ProfilePermission(profile_id=profile.id, screen=screen, can_access=True))
    db.commit()
    db.refresh(profile)
    return get_profile_by_id(db, profile.id)  # type: ignore[return-value]


def delete_profile(db: Session, profile: Profile) -> None:
    db.delete(profile)
    db.commit()
