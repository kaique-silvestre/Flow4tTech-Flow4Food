
from sqlalchemy.orm import Session

from src.models.user_permissions import UserPermission


def list_by_user(db: Session, user_id: int) -> list[UserPermission]:
    return (
        db.query(UserPermission)
        .filter(UserPermission.user_id == user_id, UserPermission.can_access == True)  # noqa: E712
        .all()
    )


def replace_all(db: Session, user_id: int, tenant_id: int, screens: list[str]) -> list[UserPermission]:
    db.query(UserPermission).filter(UserPermission.user_id == user_id).delete()
    for screen in screens:
        db.add(UserPermission(user_id=user_id, tenant_id=tenant_id, screen=screen, can_access=True))
    db.commit()
    return list_by_user(db, user_id)
