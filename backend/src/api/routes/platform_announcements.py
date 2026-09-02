from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.dependencies import require_platform_admin
from src.core.database import get_platform_db
from src.repositories import announcements_repository
from src.services import audit_service

router = APIRouter(dependencies=[Depends(require_platform_admin)])


class AnnouncementCreate(BaseModel):
    title: str
    body: str
    expires_at: Optional[datetime] = None  # noqa: UP045
    target: str = "all"
    tenant_ids: list[int] = []


class AnnouncementResponse(BaseModel):
    id: int
    title: str
    body: str
    expires_at: Optional[datetime]  # noqa: UP045
    target: str
    is_active: bool
    created_at: Optional[datetime]  # noqa: UP045
    read_count: int


@router.get(
    "/announcements",
    response_model=list[AnnouncementResponse],
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def list_announcements(
    db: Session = Depends(get_platform_db),
) -> list[AnnouncementResponse]:
    rows = announcements_repository.list_with_read_counts(db)
    return [AnnouncementResponse(**r) for r in rows]


@router.post(
    "/announcements",
    response_model=AnnouncementResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["platform"],
)
def create_announcement(
    body: AnnouncementCreate,
    background_tasks: BackgroundTasks,
    payload: dict = Depends(require_platform_admin),
    db: Session = Depends(get_platform_db),
) -> AnnouncementResponse:
    ann = announcements_repository.create(
        db,
        title=body.title,
        body=body.body,
        expires_at=body.expires_at,
        target=body.target,
        tenant_ids=body.tenant_ids,
        created_by=payload.get("platform_admin_id"),
    )
    rows = announcements_repository.list_with_read_counts(db)
    row = next((r for r in rows if r["id"] == ann.id), None)
    if row is None:
        row = {
            "id": ann.id,
            "title": ann.title,
            "body": ann.body,
            "expires_at": ann.expires_at,
            "target": ann.target,
            "is_active": ann.is_active,
            "created_at": ann.created_at,
            "read_count": 0,
        }
    actor_id = payload.get("platform_admin_id") or payload.get("admin_id") or payload.get("sub")
    try:
        actor_id = int(actor_id) if actor_id is not None else None
    except (TypeError, ValueError):
        actor_id = None
    background_tasks.add_task(
        audit_service.log_background,
        "platform.announcement.create",
        tenant_id=body.tenant_ids[0] if len(body.tenant_ids) == 1 else None,
        user_id=actor_id,
        entity="PlatformAnnouncement",
        entity_id=ann.id,
        after={
            "title": ann.title,
            "target": ann.target,
            "tenant_ids": body.tenant_ids,
            "expires_at": ann.expires_at.isoformat() if ann.expires_at else None,
        },
    )
    return AnnouncementResponse(**row)
