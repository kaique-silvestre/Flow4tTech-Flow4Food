from typing import Optional

from sqlalchemy.orm import Session

from src.models.platform_admin import PlatformAdmin


def get_by_email(db: Session, email: str) -> Optional[PlatformAdmin]:  # noqa: UP045
    return db.query(PlatformAdmin).filter(PlatformAdmin.email == email).first()


def get_by_id(db: Session, admin_id: int) -> Optional[PlatformAdmin]:  # noqa: UP045
    return db.query(PlatformAdmin).filter(PlatformAdmin.id == admin_id).first()


def create(db: Session, email: str, name: str, password_hash: str) -> PlatformAdmin:
    admin = PlatformAdmin(email=email, name=name, password_hash=password_hash)
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin
