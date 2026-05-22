from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from src.models.system_users import PasswordReset, SystemUser


def get_valid_reset(db: Session, token: str) -> Optional[PasswordReset]:
    return (
        db.query(PasswordReset)
        .options(joinedload(PasswordReset.user))
        .filter(
            PasswordReset.token == token,
            PasswordReset.used_at.is_(None),
            PasswordReset.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )


def get_reset_by_token(db: Session, token: str) -> Optional[PasswordReset]:
    return db.query(PasswordReset).filter(PasswordReset.token == token).first()


def create_reset(db: Session, reset: PasswordReset) -> PasswordReset:
    db.add(reset)
    db.commit()
    db.refresh(reset)
    return reset


def invalidate_user_resets(db: Session, user_id: int) -> None:
    """Mark all unused tokens for user as used before issuing a new one."""
    db.query(PasswordReset).filter(
        PasswordReset.user_id == user_id,
        PasswordReset.used_at.is_(None),
    ).update({"used_at": datetime.now(timezone.utc)})
    db.commit()
