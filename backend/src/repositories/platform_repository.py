from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.assinaturas import Assinatura
from src.models.profiles import Profile
from src.models.system_users import SystemUser
from src.models.tenants import Tenant


def list_tenants(db: Session, status_filter: Optional[str] = None) -> list[dict]:  # noqa: UP045
    stmt = (
        select(
            Tenant.id,
            Tenant.nome_fantasia,
            Tenant.cnpj,
            Tenant.status.label("status_tenant"),
            Assinatura.status.label("status_assinatura"),
            Assinatura.data_vencimento,
        )
        .outerjoin(Assinatura, Assinatura.tenant_id == Tenant.id)
        .order_by(Tenant.id)
    )
    if status_filter:
        stmt = stmt.where(Assinatura.status == status_filter)
    rows = db.execute(stmt).all()
    return [
        {
            "id": r.id,
            "nome_fantasia": r.nome_fantasia,
            "cnpj": r.cnpj,
            "status_tenant": r.status_tenant,
            "status_assinatura": r.status_assinatura,
            "data_vencimento": r.data_vencimento,
        }
        for r in rows
    ]


def get_tenant_users(db: Session, tenant_id: int) -> list[dict]:
    stmt = (
        select(
            SystemUser.id,
            SystemUser.name,
            SystemUser.username,
            SystemUser.last_login,
            SystemUser.is_active,
            Profile.name.label("profile_name"),
        )
        .join(Profile, Profile.id == SystemUser.profile_id)
        .where(SystemUser.tenant_id == tenant_id)
        .order_by(SystemUser.id)
    )
    rows = db.execute(stmt).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "username": r.username,
            "profile_name": r.profile_name,
            "last_login": r.last_login,
            "is_active": r.is_active,
        }
        for r in rows
    ]


def update_assinatura_status(db: Session, tenant_id: int, new_status: str) -> Assinatura:
    assinatura = db.execute(
        select(Assinatura).where(Assinatura.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if assinatura is None:
        now = datetime.now(timezone.utc)
        assinatura = Assinatura(
            tenant_id=tenant_id,
            status=new_status,
            data_inicio=now,
            created_at=now,
            updated_at=now,
        )
        db.add(assinatura)
    else:
        assinatura.status = new_status
        assinatura.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(assinatura)
    return assinatura
