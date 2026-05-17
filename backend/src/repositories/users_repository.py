from typing import Optional

from sqlalchemy.orm import Session, joinedload

from src.models.profiles import Profile
from src.models.system_users import SystemUser


def _with_profile(q):
    return q.options(
        joinedload(SystemUser.profile).joinedload(Profile.permissions)
    )


def get_user_by_username(db: Session, tenant_id: int, username: str) -> Optional[SystemUser]:
    return _with_profile(
        db.query(SystemUser).filter(SystemUser.tenant_id == tenant_id, SystemUser.username == username)
    ).first()


def get_user_by_email(db: Session, email: str) -> Optional[SystemUser]:
    return _with_profile(
        db.query(SystemUser).filter(SystemUser.email == email)
    ).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[SystemUser]:
    return _with_profile(
        db.query(SystemUser).filter(SystemUser.id == user_id)
    ).first()
