from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from src.models.platform_announcements import (
    AnnouncementRead,
    AnnouncementTarget,
    PlatformAnnouncement,
)


def list_with_read_counts(db: Session) -> list[dict]:
    stmt = (
        select(
            PlatformAnnouncement,
            func.count(AnnouncementRead.id).label("read_count"),
        )
        .outerjoin(AnnouncementRead, AnnouncementRead.announcement_id == PlatformAnnouncement.id)
        .group_by(PlatformAnnouncement.id)
        .order_by(PlatformAnnouncement.created_at.desc())
    )
    rows = db.execute(stmt).all()
    return [
        {
            "id": ann.id,
            "title": ann.title,
            "body": ann.body,
            "expires_at": ann.expires_at,
            "target": ann.target,
            "is_active": ann.is_active,
            "created_at": ann.created_at,
            "read_count": count,
        }
        for ann, count in rows
    ]


def create(
    db: Session,
    title: str,
    body: str,
    expires_at: datetime | None,
    target: str,
    tenant_ids: list[int],
    created_by: int | None,
) -> PlatformAnnouncement:
    now = datetime.now(timezone.utc)
    ann = PlatformAnnouncement(
        title=title,
        body=body,
        expires_at=expires_at,
        target=target,
        is_active=True,
        created_by=created_by,
        created_at=now,
    )
    db.add(ann)
    db.flush()

    if target == "specific":
        for tid in tenant_ids:
            db.add(AnnouncementTarget(announcement_id=ann.id, tenant_id=tid))

    db.commit()
    db.refresh(ann)
    return ann


def list_active_for_user(db: Session, tenant_id: int, user_id: int) -> list[PlatformAnnouncement]:
    now = datetime.now(timezone.utc)

    already_read = select(AnnouncementRead.announcement_id).where(
        AnnouncementRead.user_id == user_id
    )

    targeted = select(AnnouncementTarget.announcement_id).where(
        AnnouncementTarget.tenant_id == tenant_id
    )

    stmt = (
        select(PlatformAnnouncement)
        .where(
            PlatformAnnouncement.is_active.is_(True),
            or_(
                PlatformAnnouncement.expires_at.is_(None),
                PlatformAnnouncement.expires_at > now,
            ),
            PlatformAnnouncement.id.not_in(already_read),
            or_(
                PlatformAnnouncement.target == "all",
                and_(
                    PlatformAnnouncement.target == "specific",
                    PlatformAnnouncement.id.in_(targeted),
                ),
            ),
        )
        .order_by(PlatformAnnouncement.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def is_visible_to_tenant(db: Session, announcement_id: int, tenant_id: int) -> bool:
    targeted = select(AnnouncementTarget.announcement_id).where(
        AnnouncementTarget.tenant_id == tenant_id
    )
    stmt = select(PlatformAnnouncement.id).where(
        PlatformAnnouncement.id == announcement_id,
        or_(
            PlatformAnnouncement.target == "all",
            and_(
                PlatformAnnouncement.target == "specific",
                PlatformAnnouncement.id.in_(targeted),
            ),
        ),
    )
    return db.execute(stmt).scalar_one_or_none() is not None


def mark_read(db: Session, announcement_id: int, user_id: int, tenant_id: int) -> None:
    existing = db.execute(
        select(AnnouncementRead).where(
            AnnouncementRead.announcement_id == announcement_id,
            AnnouncementRead.user_id == user_id,
        )
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            AnnouncementRead(
                announcement_id=announcement_id,
                user_id=user_id,
                tenant_id=tenant_id,
                read_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
