from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from src.models.refresh_tokens import RefreshToken


def create(db: Session, user_id: int, token_hash: str, expires_at: datetime) -> RefreshToken:
    rt = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    db.add(rt)
    db.commit()
    db.refresh(rt)
    return rt


def get_by_hash(db: Session, token_hash: str) -> Optional[RefreshToken]:
    return db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()


def revoke(db: Session, record_id: int) -> None:
    rt = db.query(RefreshToken).filter(RefreshToken.id == record_id).first()
    if rt:
        rt.revoked_at = datetime.now(timezone.utc)
        db.commit()


def revoke_all_for_user(db: Session, user_id: int) -> None:
    now = datetime.now(timezone.utc)
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked_at.is_(None),
    ).update({"revoked_at": now})
    db.commit()


def delete_expired(db: Session) -> int:
    now = datetime.now(timezone.utc)
    deleted = db.query(RefreshToken).filter(RefreshToken.expires_at < now).delete()
    db.commit()
    return deleted
