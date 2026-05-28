from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.assinaturas import Assinatura
from src.models.system_users import SystemUser
from src.models.tenants import Tenant
from src.repositories.tenant_repository import (
    clone_profiles_from_seed,
    create_assinatura,
    create_tenant,
    get_assinatura_by_tenant,
    get_tenant_by_id,
    list_tenants,
    set_rls_tenant,
    update_tenant,
)
from src.repositories.users_repository import get_user_by_email, get_user_by_username
from src.schemas.tenants import AssinaturaInfo, TenantCreate, TenantResponse, TenantUpdate
from src.services.auth_service import hash_password


def _assinatura_info(assinatura: Optional[Assinatura]) -> Optional[AssinaturaInfo]:
    if assinatura is None:
        return None
    return AssinaturaInfo(
        id=assinatura.id,
        status=assinatura.status,
        data_inicio=assinatura.data_inicio,
        data_vencimento=assinatura.data_vencimento,
    )


def _to_response(tenant: Tenant, assinatura: Optional[Assinatura] = None) -> TenantResponse:
    return TenantResponse(
        id=tenant.id,
        nome_fantasia=tenant.nome_fantasia,
        cnpj=tenant.cnpj,
        status=tenant.status,
        admin_user_id=tenant.admin_user_id,
        created_at=tenant.created_at,
        assinatura=_assinatura_info(assinatura),
    )


def criar_tenant(db: Session, data: TenantCreate) -> TenantResponse:
    if get_user_by_email(db, data.admin_email):
        raise AppError(
            code=ErrorCode.CONFLICT,
            message="Email já em uso",
            field="admin_email",
            http_status=409,
        )

    try:
        now = datetime.now(timezone.utc)
        # 1. Create tenant
        tenant = Tenant(
            nome_fantasia=data.nome_fantasia,
            cnpj=data.cnpj,
            status="ativo",
            created_at=now,
        )
        tenant = create_tenant(db, tenant)

        # 2. Clone profiles from seed tenant (id=1) — sets RLS to tenant_id=1 internally
        cloned_profiles = clone_profiles_from_seed(db, tenant.id)

        # Switch RLS context to new tenant for subsequent SELECTs (refresh, username check)
        set_rls_tenant(db, tenant.id)

        # 3. Find the Admin profile among cloned
        admin_profile = next((p for p in cloned_profiles if p.name == "Admin"), None)
        if admin_profile is None:
            raise AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="Perfil Admin não encontrado no seed",
                http_status=500,
            )

        # 4. Check username uniqueness in new tenant context
        if get_user_by_username(db, tenant.id, data.admin_username):
            raise AppError(
                code=ErrorCode.CONFLICT,
                message="Username já em uso",
                field="admin_username",
                http_status=409,
            )

        # 5. Create admin user
        admin_user = SystemUser(
            tenant_id=tenant.id,
            profile_id=admin_profile.id,
            name=data.admin_name,
            username=data.admin_username,
            email=data.admin_email,
            password_hash=hash_password(data.admin_password),
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(admin_user)
        db.flush()
        db.refresh(admin_user)

        # 6. Create trial subscription
        assinatura = Assinatura(tenant_id=tenant.id, status="trial", data_inicio=now, created_at=now, updated_at=now)
        assinatura = create_assinatura(db, assinatura)

        # 7. Link admin_user_id back to tenant
        tenant.admin_user_id = admin_user.id
        db.flush()

        db.commit()
        db.refresh(tenant)
        db.refresh(assinatura)
    except AppError:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="Erro ao criar tenant",
            http_status=500,
        ) from exc

    return _to_response(tenant, assinatura)


def get_tenant(db: Session, tenant_id: int) -> TenantResponse:
    tenant = get_tenant_by_id(db, tenant_id)
    if tenant is None:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Tenant não encontrado", http_status=404)
    assinatura = get_assinatura_by_tenant(db, tenant_id)
    return _to_response(tenant, assinatura)


def update_existing_tenant(db: Session, tenant_id: int, data: TenantUpdate) -> TenantResponse:
    tenant = get_tenant_by_id(db, tenant_id)
    if tenant is None:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Tenant não encontrado", http_status=404)
    if data.nome_fantasia is not None:
        tenant.nome_fantasia = data.nome_fantasia
    if data.status is not None:
        tenant.status = data.status
    tenant = update_tenant(db, tenant)
    db.commit()
    db.refresh(tenant)
    assinatura = get_assinatura_by_tenant(db, tenant_id)
    return _to_response(tenant, assinatura)


def get_all_tenants(db: Session) -> list[TenantResponse]:
    tenants = list_tenants(db)
    result = []
    for t in tenants:
        assinatura = get_assinatura_by_tenant(db, t.id)
        result.append(_to_response(t, assinatura))
    return result
