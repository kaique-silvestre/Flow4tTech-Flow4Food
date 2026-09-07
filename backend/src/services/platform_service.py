from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.profiles import ProfilePermission
from src.models.system_users import SystemUser
from src.models.user_permissions import UserPermission
from src.services import audit_service


def resolve_impersonation_permissions(db: Session, user: SystemUser) -> list[str]:
    perms = db.execute(
        select(UserPermission.screen).where(UserPermission.user_id == user.id)
    ).scalars().all()
    if not perms and user.profile_id:
        perms = db.execute(
            select(ProfilePermission.screen).where(ProfilePermission.profile_id == user.profile_id)
        ).scalars().all()
    return list(perms)


def audited_field_update(
    background_tasks: BackgroundTasks,
    *,
    action: str,
    tenant_id: Optional[int],
    actor_id: Optional[int],
    entity: str,
    entity_id: int,
    before_row: dict,
    after_row: dict,
    fields: tuple[str, ...],
    extra_after: Optional[dict] = None,
) -> None:
    before = {k: before_row[k] for k in fields if k in before_row}
    after = {k: after_row[k] for k in fields} | (extra_after or {})
    background_tasks.add_task(
        audit_service.log_background,
        action,
        tenant_id=tenant_id,
        user_id=actor_id,
        entity=entity,
        entity_id=entity_id,
        before=before,
        after=after,
    )
