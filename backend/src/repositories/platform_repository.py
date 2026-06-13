from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from src.models.assinaturas import Assinatura
from src.models.platform_settings import PlatformSettings
from src.models.profiles import Profile
from src.models.system_users import SystemUser
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
