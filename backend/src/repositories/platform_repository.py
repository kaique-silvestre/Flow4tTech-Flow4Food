from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from src.models.assinaturas import Assinatura, AssinaturaHistory
from src.models.platform_admin import PlatformAdmin
from src.models.platform_settings import PlatformSettings
from src.models.profiles import Profile, ProfilePermission
from src.models.system_users import SystemUser
from src.models.tenant_features import TenantFeature
from src.models.tenants import Tenant


def list_tenants(db: Session, status_filter: Optional[str] = None) -> list[dict]:  # noqa: UP045
    user_count_sq = (
        select(func.count(SystemUser.id))
        .where(SystemUser.tenant_id == Tenant.id)
        .correlate(Tenant)
        .scalar_subquery()
    )
    stmt = (
        select(
            Tenant.id,
            Tenant.nome_fantasia,
            Tenant.cnpj,
            Tenant.max_users,
            Tenant.status.label("status_tenant"),
            Assinatura.status.label("status_assinatura"),
            Assinatura.data_vencimento,
            user_count_sq.label("qtd_usuarios"),
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
            "max_users": r.max_users,
            "status_tenant": r.status_tenant,
            "status_assinatura": r.status_assinatura,
            "data_vencimento": r.data_vencimento,
            "qtd_usuarios": int(r.qtd_usuarios or 0),
        }
        for r in rows
    ]


def get_setting(db: Session, key: str) -> Optional[str]:  # noqa: UP045
    row = db.execute(
        select(PlatformSettings.value).where(PlatformSettings.key == key)
    ).scalar_one_or_none()
    return row


def upsert_setting(db: Session, key: str, value: str) -> PlatformSettings:
    setting = db.execute(
        select(PlatformSettings).where(PlatformSettings.key == key)
    ).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if setting is None:
        setting = PlatformSettings(key=key, value=value, updated_at=now)
        db.add(setting)
    else:
        setting.value = value
        setting.updated_at = now
    db.commit()
    db.refresh(setting)
    return setting


def list_settings(db: Session) -> list[PlatformSettings]:
    rows = db.execute(select(PlatformSettings).order_by(PlatformSettings.key)).scalars().all()
    return list(rows)


def create_platform_tenant(
    db: Session,
    nome_fantasia: str,
    cnpj: Optional[str],  # noqa: UP045
    endereco: Optional[str],  # noqa: UP045
    telefone: Optional[str],  # noqa: UP045
    max_users: int,
    trial_days: int,
) -> dict:
    now = datetime.now(timezone.utc)
    tenant = Tenant(
        nome_fantasia=nome_fantasia,
        cnpj=cnpj or None,
        endereco=endereco or None,
        telefone=telefone or None,
        max_users=max_users,
        status="ativo",
        created_at=now,
    )
    db.add(tenant)
    db.flush()
    db.refresh(tenant)

    assinatura = Assinatura(
        tenant_id=tenant.id,
        status="trial",
        data_inicio=now,
        data_vencimento=now + timedelta(days=trial_days),
        created_at=now,
        updated_at=now,
    )
    db.add(assinatura)
    db.commit()
    db.refresh(tenant)
    db.refresh(assinatura)

    return {
        "id": tenant.id,
        "nome_fantasia": tenant.nome_fantasia,
        "cnpj": tenant.cnpj,
        "status_tenant": tenant.status,
        "status_assinatura": assinatura.status,
        "data_vencimento": assinatura.data_vencimento,
        "max_users": tenant.max_users,
        "qtd_usuarios": 0,
    }


def get_tenant_users(db: Session, tenant_id: int) -> list[dict]:
    stmt = (
        select(
            SystemUser.id,
            SystemUser.name,
            SystemUser.username,
            SystemUser.email,
            SystemUser.profile_id,
            SystemUser.last_login,
            SystemUser.is_active,
            Profile.name.label("profile_name"),
        )
        .outerjoin(Profile, Profile.id == SystemUser.profile_id)
        .where(SystemUser.tenant_id == tenant_id)
        .order_by(SystemUser.id)
    )
    rows = db.execute(stmt).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "username": r.username,
            "email": r.email,
            "profile_id": r.profile_id,
            "profile_name": r.profile_name,
            "last_login": r.last_login,
            "is_active": r.is_active,
        }
        for r in rows
    ]


_COCKPIT_SQL = text("""
SELECT
  t.id,
  t.nome_fantasia,
  t.cnpj,
  t.created_at                                                AS tenant_created_at,
  t.status                                                    AS status_tenant,
  a.status                                                    AS status_assinatura,
  EXTRACT(DAY FROM NOW() - t.created_at)::int                 AS dias_cliente,
  (SELECT MAX(u.last_login)
   FROM system_users u WHERE u.tenant_id = t.id)             AS ultimo_login,
  (SELECT COUNT(*)
   FROM comandas c
   WHERE c.tenant_id = t.id
     AND DATE_TRUNC('month', c.created_at) = DATE_TRUNC('month', NOW()))
                                                              AS comandas_mes,
  (SELECT COALESCE(SUM(c.total), 0)
   FROM comandas c
   WHERE c.tenant_id = t.id
     AND c.status = 'fechada'
     AND DATE_TRUNC('month', c.created_at) = DATE_TRUNC('month', NOW()))
                                                              AS faturamento_mes,
  (SELECT COUNT(DISTINCT u.id)
   FROM system_users u
   WHERE u.tenant_id = t.id
     AND u.last_login >= NOW() - INTERVAL '30 days')          AS usuarios_ativos_30d,
  (SELECT COUNT(*)
   FROM compras cp
   WHERE cp.tenant_id = t.id
     AND DATE_TRUNC('month', cp.created_at) = DATE_TRUNC('month', NOW()))
                                                              AS compras_mes
FROM tenants t
LEFT JOIN assinaturas a ON a.tenant_id = t.id
""")


def get_cockpit_metrics(
    db: Session, status_filter: Optional[str] = None  # noqa: UP045
) -> list[dict]:
    sql = _COCKPIT_SQL
    if status_filter:
        sql = text(str(sql.text) + " WHERE a.status = :status_filter ORDER BY t.id")
        rows = db.execute(sql, {"status_filter": status_filter}).all()
    else:
        sql = text(str(sql.text) + " ORDER BY t.id")
        rows = db.execute(sql).all()
    return [_row_to_cockpit_dict(r) for r in rows]


def get_tenant_cockpit_metrics(db: Session, tenant_id: int) -> Optional[dict]:  # noqa: UP045
    sql = text(str(_COCKPIT_SQL.text) + " WHERE t.id = :tenant_id")
    row = db.execute(sql, {"tenant_id": tenant_id}).first()
    if row is None:
        return None
    return _row_to_cockpit_dict(row)


def _row_to_cockpit_dict(r: object) -> dict:
    return {
        "id": r.id,  # type: ignore[attr-defined]
        "nome_fantasia": r.nome_fantasia,  # type: ignore[attr-defined]
        "cnpj": r.cnpj,  # type: ignore[attr-defined]
        "status_tenant": r.status_tenant,  # type: ignore[attr-defined]
        "status_assinatura": r.status_assinatura,  # type: ignore[attr-defined]
        "dias_cliente": int(r.dias_cliente or 0),  # type: ignore[attr-defined]
        "ultimo_login": r.ultimo_login,  # type: ignore[attr-defined]
        "comandas_mes": int(r.comandas_mes or 0),  # type: ignore[attr-defined]
        "faturamento_mes": float(r.faturamento_mes or 0),  # type: ignore[attr-defined]
        "usuarios_ativos_30d": int(r.usuarios_ativos_30d or 0),  # type: ignore[attr-defined]
        "compras_mes": int(r.compras_mes or 0),  # type: ignore[attr-defined]
    }


def update_assinatura_status(
    db: Session,
    tenant_id: int,
    new_status: str,
    data_vencimento: datetime | None = None,
    changed_by: int | None = None,
) -> Assinatura:
    assinatura = db.execute(
        select(Assinatura).where(Assinatura.tenant_id == tenant_id)
    ).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if assinatura is None:
        assinatura = Assinatura(
            tenant_id=tenant_id,
            status=new_status,
            data_inicio=now,
            data_vencimento=data_vencimento,
            created_at=now,
            updated_at=now,
        )
        db.add(assinatura)
        db.flush()
    else:
        old_status = assinatura.status
        assinatura.status = new_status
        assinatura.updated_at = now
        if data_vencimento is not None:
            assinatura.data_vencimento = data_vencimento
        db.flush()
        history = AssinaturaHistory(
            assinatura_id=assinatura.id,
            from_status=old_status,
            to_status=new_status,
            changed_by=changed_by,
            created_at=now,
        )
        db.add(history)
    db.commit()
    db.refresh(assinatura)
    return assinatura


def get_assinatura_history(db: Session, tenant_id: int) -> list[dict]:
    assinatura = db.execute(
        select(Assinatura).where(Assinatura.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if assinatura is None:
        return []
    rows = db.execute(
        select(
            AssinaturaHistory.id,
            AssinaturaHistory.from_status,
            AssinaturaHistory.to_status,
            AssinaturaHistory.changed_by,
            AssinaturaHistory.created_at,
            PlatformAdmin.name.label("changed_by_name"),
        )
        .outerjoin(PlatformAdmin, PlatformAdmin.id == AssinaturaHistory.changed_by)
        .where(AssinaturaHistory.assinatura_id == assinatura.id)
        .order_by(AssinaturaHistory.created_at.desc())
    ).all()
    return [
        {
            "id": r.id,
            "from_status": r.from_status,
            "to_status": r.to_status,
            "changed_by": r.changed_by,
            "changed_by_name": r.changed_by_name,
            "created_at": r.created_at,
        }
        for r in rows
    ]


def get_tenant_detail(db: Session, tenant_id: int) -> Optional[dict]:  # noqa: UP045
    row = db.execute(
        select(
            Tenant.id,
            Tenant.nome_fantasia,
            Tenant.cnpj,
            Tenant.endereco,
            Tenant.telefone,
            Tenant.status,
            Tenant.max_users,
            Tenant.created_at,
            Assinatura.status.label("status_assinatura"),
            Assinatura.data_vencimento,
            Assinatura.data_inicio,
        )
        .outerjoin(Assinatura, Assinatura.tenant_id == Tenant.id)
        .where(Tenant.id == tenant_id)
    ).first()
    if row is None:
        return None
    user_count = db.execute(
        select(func.count(SystemUser.id)).where(SystemUser.tenant_id == tenant_id)
    ).scalar_one()
    return {
        "id": row.id,
        "nome_fantasia": row.nome_fantasia,
        "cnpj": row.cnpj,
        "endereco": row.endereco,
        "telefone": row.telefone,
        "status": row.status,
        "max_users": row.max_users,
        "created_at": row.created_at,
        "status_assinatura": row.status_assinatura,
        "data_vencimento": row.data_vencimento,
        "data_inicio": row.data_inicio,
        "qtd_usuarios": int(user_count or 0),
    }


def update_tenant(
    db: Session,
    tenant_id: int,
    nome_fantasia: str | None = None,
    cnpj: str | None = None,
    endereco: str | None = None,
    telefone: str | None = None,
    max_users: int | None = None,
) -> Optional[dict]:  # noqa: UP045
    tenant = db.execute(select(Tenant).where(Tenant.id == tenant_id)).scalar_one_or_none()
    if tenant is None:
        return None
    if nome_fantasia is not None:
        tenant.nome_fantasia = nome_fantasia
    if cnpj is not None:
        tenant.cnpj = cnpj
    if endereco is not None:
        tenant.endereco = endereco
    if telefone is not None:
        tenant.telefone = telefone
    if max_users is not None:
        tenant.max_users = max_users
    db.commit()
    db.refresh(tenant)
    return get_tenant_detail(db, tenant_id)


def create_tenant_user(
    db: Session,
    tenant_id: int,
    name: str,
    username: str,
    email: str | None,
    password_hash: str,
    profile_id: int | None,
    is_active: bool = True,
) -> dict:
    now = datetime.now(timezone.utc)
    user = SystemUser(
        tenant_id=tenant_id,
        name=name,
        username=username,
        email=email,
        password_hash=password_hash,
        profile_id=profile_id,
        is_active=is_active,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    profile_name = None
    if user.profile_id:
        p = db.execute(select(Profile).where(Profile.id == user.profile_id)).scalar_one_or_none()
        profile_name = p.name if p else None
    return {
        "id": user.id,
        "name": user.name,
        "username": user.username,
        "email": user.email,
        "profile_id": user.profile_id,
        "profile_name": profile_name,
        "is_active": user.is_active,
        "last_login": user.last_login,
    }


def update_tenant_user(
    db: Session,
    tenant_id: int,
    user_id: int,
    name: str | None = None,
    username: str | None = None,
    email: str | None = None,
    password_hash: str | None = None,
    profile_id: int | None = None,
    is_active: bool | None = None,
) -> Optional[dict]:  # noqa: UP045
    user = db.execute(
        select(SystemUser).where(SystemUser.id == user_id, SystemUser.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if user is None:
        return None
    if name is not None:
        user.name = name
    if username is not None:
        user.username = username
    if email is not None:
        user.email = email
    if password_hash is not None:
        user.password_hash = password_hash
    if profile_id is not None:
        user.profile_id = profile_id
    if is_active is not None:
        user.is_active = is_active
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    profile_name = None
    if user.profile_id:
        p = db.execute(select(Profile).where(Profile.id == user.profile_id)).scalar_one_or_none()
        profile_name = p.name if p else None
    return {
        "id": user.id,
        "name": user.name,
        "username": user.username,
        "email": user.email,
        "profile_id": user.profile_id,
        "profile_name": profile_name,
        "is_active": user.is_active,
        "last_login": user.last_login,
    }


def get_tenant_profiles(db: Session, tenant_id: int) -> list[dict]:
    profiles = db.execute(
        select(Profile).where(Profile.tenant_id == tenant_id).order_by(Profile.id)
    ).scalars().all()
    result = []
    for profile in profiles:
        perms = db.execute(
            select(ProfilePermission.screen)
            .where(ProfilePermission.profile_id == profile.id)
        ).scalars().all()
        user_count = db.execute(
            select(func.count(SystemUser.id)).where(SystemUser.profile_id == profile.id)
        ).scalar_one()
        result.append({
            "id": profile.id,
            "name": profile.name,
            "description": profile.description,
            "is_active": profile.is_active,
            "permissions": list(perms),
            "user_count": int(user_count or 0),
        })
    return result


def update_tenant_profile(
    db: Session,
    tenant_id: int,
    profile_id: int,
    permissions: list[str] | None = None,
    is_active: bool | None = None,
) -> Optional[dict]:  # noqa: UP045
    profile = db.execute(
        select(Profile).where(Profile.id == profile_id, Profile.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if profile is None:
        return None
    if is_active is not None:
        profile.is_active = is_active
    if permissions is not None:
        db.execute(
            delete(ProfilePermission).where(ProfilePermission.profile_id == profile_id)
        )
        now = datetime.now(timezone.utc)
        for screen in permissions:
            db.add(ProfilePermission(profile_id=profile_id, screen=screen, created_at=now))
    db.commit()
    all_profiles = get_tenant_profiles(db, tenant_id)
    for p in all_profiles:
        if p["id"] == profile_id:
            return p
    return None


def get_tenant_features(db: Session, tenant_id: int) -> list[dict]:
    rows = db.execute(
        select(TenantFeature).where(TenantFeature.tenant_id == tenant_id)
    ).scalars().all()
    return [{"feature": r.feature, "enabled": r.enabled} for r in rows]


def upsert_tenant_features(db: Session, tenant_id: int, features: dict) -> list[dict]:
    now = datetime.now(timezone.utc)
    for feature, enabled in features.items():
        existing = db.execute(
            select(TenantFeature).where(
                TenantFeature.tenant_id == tenant_id,
                TenantFeature.feature == feature,
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(TenantFeature(tenant_id=tenant_id, feature=feature, enabled=enabled, updated_at=now))
        else:
            existing.enabled = enabled
            existing.updated_at = now
    db.commit()
    return get_tenant_features(db, tenant_id)
