from typing import Optional

from sqlalchemy.orm import Session, joinedload

from src.models.profiles import Profile
from src.models.system_users import SystemUser


def _with_profile(q):
    return q.options(joinedload(SystemUser.profile).joinedload(Profile.permissions))


def get_user_by_username(db: Session, tenant_id: int, username: str) -> Optional[SystemUser]:
    return _with_profile(
        db.query(SystemUser).filter(SystemUser.tenant_id == tenant_id, SystemUser.username == username)
    ).first()


def get_user_by_username_global(db: Session, username: str) -> Optional[SystemUser]:
    return _with_profile(
        db.query(SystemUser).filter(SystemUser.username == username)
    ).first()


def get_user_by_email(db: Session, email: str) -> Optional[SystemUser]:
    return _with_profile(
        db.query(SystemUser).filter(SystemUser.email == email)
    ).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[SystemUser]:
    return _with_profile(
        db.query(SystemUser).filter(SystemUser.id == user_id)
    ).first()


def list_users(
    db: Session,
    tenant_id: int,
    search: Optional[str] = None,
    profile_id: Optional[int] = None,
) -> list[SystemUser]:
    q = _with_profile(db.query(SystemUser).filter(SystemUser.tenant_id == tenant_id))
    if search:
        like = f"%{search}%"
        q = q.filter(
            (SystemUser.name.ilike(like)) | (SystemUser.username.ilike(like))
        )
    if profile_id is not None:
        q = q.filter(SystemUser.profile_id == profile_id)
    return q.order_by(SystemUser.name).all()


def count_active_admins(db: Session, tenant_id: int, admin_profile_id: int) -> int:
    return (
        db.query(SystemUser)
        .filter(
            SystemUser.tenant_id == tenant_id,
            SystemUser.profile_id == admin_profile_id,
            SystemUser.is_active == True,  # noqa: E712
        )
        .count()
    )


def create_user(db: Session, user: SystemUser) -> SystemUser:
    db.add(user)
    db.commit()
    db.refresh(user)
    return get_user_by_id(db, user.id)  # type: ignore[return-value]


def update_user(db: Session, user: SystemUser) -> SystemUser:
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: SystemUser) -> None:
    db.delete(user)
    db.commit()
