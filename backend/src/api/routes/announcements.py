from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user
from src.core.database import get_platform_db
from src.repositories import announcements_repository

router = APIRouter()


class AnnouncementItem(BaseModel):
    id: int
    title: str
    body: str
    expires_at: Optional[datetime]  # noqa: UP045
    created_at: Optional[datetime]  # noqa: UP045


@router.get(
    "/announcements",
    response_model=list[AnnouncementItem],
    status_code=status.HTTP_200_OK,
    tags=["announcements"],
)
def get_active_announcements(
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_platform_db),
) -> list[AnnouncementItem]:
    tenant_id = payload["tenant_id"]
    user_id = payload["user_id"]
    items = announcements_repository.list_active_for_user(db, tenant_id, user_id)
    return [
        AnnouncementItem(
            id=a.id,
            title=a.title,
            body=a.body,
            expires_at=a.expires_at,
            created_at=a.created_at,
        )
        for a in items
    ]


@router.post(
    "/announcements/{announcement_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["announcements"],
)
def mark_announcement_read(
    announcement_id: int,
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_platform_db),
) -> None:
    tenant_id = payload["tenant_id"]
    user_id = payload["user_id"]
    if not announcements_repository.is_visible_to_tenant(db, announcement_id, tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    announcements_repository.mark_read(db, announcement_id, user_id, tenant_id)
