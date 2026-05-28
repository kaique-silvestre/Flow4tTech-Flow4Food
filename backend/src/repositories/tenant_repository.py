import contextlib
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.models.assinaturas import Assinatura
from src.models.profiles import Profile, ProfilePermission
from src.models.tenants import Tenant


def create_tenant(db: Session, tenant: Tenant) -> Tenant:
    db.add(tenant)
    db.flush()
    db.refresh(tenant)
    return tenant


def get_tenant_by_id(db: Session, tenant_id: int) -> Optional[Tenant]:
    return db.query(Tenant).filter(Tenant.id == tenant_id).first()


def update_tenant(db: Session, tenant: Tenant) -> Tenant:
    db.flush()
    db.refresh(tenant)
    return tenant


def list_tenants(db: Session) -> list[Tenant]:
    return db.query(Tenant).order_by(Tenant.id).all()


def get_assinatura_by_tenant(db: Session, tenant_id: int) -> Optional[Assinatura]:
    return db.query(Assinatura).filter(Assinatura.tenant_id == tenant_id).first()


def create_assinatura(db: Session, assinatura: Assinatura) -> Assinatura:
    db.add(assinatura)
    db.flush()
    db.refresh(assinatura)
    return assinatura


def set_rls_tenant(db: Session, tenant_id: int) -> None:
    """Set app.tenant_id for RLS in the current transaction (PostgreSQL only)."""
    with contextlib.suppress(Exception):
        db.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": str(tenant_id)})


def clone_profiles_from_seed(db: Session, new_tenant_id: int) -> list[Profile]:
    """Clone Admin/Gerente/Caixa profiles from tenant_id=1 to new_tenant_id.

    SET LOCAL app.tenant_id=1 before SELECT so PostgreSQL RLS allows reading seed profiles.
    """
    now = datetime.now(timezone.utc)
    with contextlib.suppress(Exception):
        db.execute(text("SET LOCAL app.tenant_id = '1'"))

    seed_profiles = (
        db.query(Profile)
        .filter(Profile.tenant_id == 1, Profile.is_system == True)  # noqa: E712
        .all()
    )
    cloned: list[Profile] = []
    for src in seed_profiles:
        new_profile = Profile(
            tenant_id=new_tenant_id,
            name=src.name,
            description=src.description,
            is_system=True,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(new_profile)
        db.flush()
        db.refresh(new_profile)

        for perm in src.permissions:
            db.add(
                ProfilePermission(
                    tenant_id=new_tenant_id,
                    profile_id=new_profile.id,
                    screen=perm.screen,
                    can_access=perm.can_access,
                    created_at=now,
                )
            )
        db.flush()
        cloned.append(new_profile)
    return cloned
