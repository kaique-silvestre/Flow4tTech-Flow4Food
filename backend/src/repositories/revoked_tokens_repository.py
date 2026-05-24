from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.models.revoked_tokens import RevokedToken


def revoke(db: Session, jti: str, expires_at: datetime) -> None:
    db.add(RevokedToken(jti=jti, expires_at=expires_at))
    db.commit()


def is_revoked(db: Session, jti: str) -> bool:
    return db.query(RevokedToken).filter(RevokedToken.jti == jti).first() is not None


def delete_expired(db: Session) -> int:
    now = datetime.now(timezone.utc)
    deleted = db.query(RevokedToken).filter(RevokedToken.expires_at < now).delete()
    db.commit()
    return deleted
