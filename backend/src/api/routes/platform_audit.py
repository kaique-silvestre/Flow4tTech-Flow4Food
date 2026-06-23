from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.dependencies import require_platform_admin
from src.core.database import get_platform_db
from src.models.audit_logs import AuditLog
from src.models.system_users import SystemUser
from src.models.tenants import Tenant

router = APIRouter(dependencies=[Depends(require_platform_admin)])


class AuditLogResponse(BaseModel):
    id: int
    tenant_id: Optional[int]  # noqa: UP045
    tenant_name: Optional[str]  # noqa: UP045
    user_id: Optional[int]  # noqa: UP045
    user_name: Optional[str]  # noqa: UP045
    action: str
    entity: Optional[str]  # noqa: UP045
    entity_id: Optional[int]  # noqa: UP045
    impersonated_by: Optional[int]  # noqa: UP045
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def list_audit_logs(
    tenant_id: Optional[int] = Query(None),  # noqa: UP045
    user_id: Optional[int] = Query(None),  # noqa: UP045
    action: Optional[str] = Query(None),  # noqa: UP045
    date_from: Optional[datetime] = Query(None),  # noqa: UP045
    date_to: Optional[datetime] = Query(None),  # noqa: UP045
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_platform_db),
) -> AuditLogListResponse:
    stmt = select(AuditLog)
    if tenant_id is not None:
        stmt = stmt.where(AuditLog.tenant_id == tenant_id)
    if user_id is not None:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if action is not None:
        stmt = stmt.where(AuditLog.action == action)
    if date_from is not None:
        stmt = stmt.where(AuditLog.created_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(AuditLog.created_at <= date_to)

    from sqlalchemy import func

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = db.execute(
        stmt.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()

    tenant_ids = {r.tenant_id for r in rows if r.tenant_id is not None}
    user_ids = {r.user_id for r in rows if r.user_id is not None}

    tenants: dict[int, str] = {}
    if tenant_ids:
        for t in db.execute(select(Tenant).where(Tenant.id.in_(tenant_ids))).scalars().all():
            tenants[t.id] = t.nome_fantasia

    users: dict[int, str] = {}
    if user_ids:
        for u in db.execute(select(SystemUser).where(SystemUser.id.in_(user_ids))).scalars().all():
            users[u.id] = u.name

    items = [
        AuditLogResponse(
            id=r.id,
            tenant_id=r.tenant_id,
            tenant_name=tenants.get(r.tenant_id) if r.tenant_id else None,
            user_id=r.user_id,
            user_name=users.get(r.user_id) if r.user_id else None,
            action=r.action,
            entity=r.entity,
            entity_id=r.entity_id,
            impersonated_by=r.impersonated_by,
            created_at=r.created_at,
        )
        for r in rows
    ]

    return AuditLogListResponse(items=items, total=total, page=page, page_size=page_size)
