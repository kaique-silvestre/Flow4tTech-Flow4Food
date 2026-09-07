from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core import tenant_rls
from src.core.errors import AppError, ErrorCode
from src.core.logging import get_logger
from src.models.assinaturas import Assinatura
from src.models.system_users import SystemUser
from src.models.tenants import Tenant
from src.repositories.billing_repository import get_assinatura_by_tenant
from src.repositories.tenant_repository import (
    clone_profiles_from_seed,
    create_assinatura,
    create_tenant,
    get_tenant_by_id,
    list_tenants_with_assinaturas,
    update_tenant,
)
from src.repositories.users_repository import get_user_by_email_global, get_user_by_username
from src.schemas.tenants import AssinaturaInfo, TenantCreate, TenantResponse, TenantUpdate
from src.services.auth_service import hash_password

logger = get_logger(__name__)


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


def criar_tenant(
    db: Session,
    data: TenantCreate,
    *,
    endereco: Optional[str] = None,
    telefone: Optional[str] = None,
    max_users: int = 5,
    trial_days: Optional[int] = None,
) -> TenantResponse:
    """Provision a tenant and its first owner through the shared onboarding flow.

    Platform administration can supply its extra tenant metadata, but all callers
    use the same profile cloning, owner provisioning, and transaction boundary.
    """
    if get_user_by_email_global(db, data.admin_email):
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
            endereco=endereco or None,
            telefone=telefone or None,
            max_users=max_users,
            status="ativo",
            created_at=now,
        )
        tenant = create_tenant(db, tenant)

        # 2. Clone profiles from seed tenant (id=1) — sets RLS to tenant_id=1 internally
        cloned_profiles = clone_profiles_from_seed(db, tenant.id)

        # Switch RLS context to new tenant for subsequent SELECTs (refresh, username check)
        tenant_rls.arm(db, tenant.id)

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

        # 5. Create admin user (is_owner=True — immutable, cannot be demoted or deleted)
        admin_user = SystemUser(
            tenant_id=tenant.id,
            profile_id=admin_profile.id,
            name=data.admin_name,
            username=data.admin_username,
            email=data.admin_email,
            password_hash=hash_password(data.admin_password),
            is_active=True,
            is_owner=True,
            created_at=now,
            updated_at=now,
        )
        db.add(admin_user)
        db.flush()
        db.refresh(admin_user)

        # 6. Create trial subscription
        assinatura = Assinatura(
            tenant_id=tenant.id,
            status="trial",
            data_inicio=now,
            data_vencimento=now + timedelta(days=trial_days) if trial_days is not None else None,
            created_at=now,
            updated_at=now,
        )
        assinatura = create_assinatura(db, assinatura)

        # 7. Link admin_user_id back to tenant
        tenant.admin_user_id = admin_user.id
        db.flush()

        db.commit()
        # Clean up RLS context so the connection returns clean to the pool.
        # tenants and assinaturas tables have no RLS, so refresh works without context.
        try:
            tenant_rls.clear(db)
        except Exception:
            logger.warning("tenant_rls_cleanup_failed", tenant_id=tenant.id, exc_info=True)
        db.refresh(tenant)
        db.refresh(assinatura)
    except AppError:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        if _is_cnpj_unique_violation(exc):
            raise AppError(
                code=ErrorCode.CONFLICT,
                message="CNPJ já cadastrado",
                field="cnpj",
                http_status=409,
            ) from None
        raise AppError(
            code=ErrorCode.CONFLICT,
            message="Dados do tenant conflitam com um cadastro existente",
            http_status=409,
        ) from None
    except Exception as exc:
        db.rollback()
        raise AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="Erro ao criar tenant",
            http_status=500,
        ) from exc

    return _to_response(tenant, assinatura)


def _is_cnpj_unique_violation(error: IntegrityError) -> bool:
    """Detecta se o IntegrityError foi causado pela unique constraint de `tenants.cnpj`.

    Postgres (psycopg2): usa o pgcode '23505' (unique_violation) + inspeção textual
    pra distinguir de outras colisões (ex.: email/username, tratados antes do INSERT).
    SQLite (testes): sem pgcode, cai direto pra inspeção textual da mensagem.
    """
    msg = str(error.orig).lower()
    return "cnpj" in msg


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
    return [
        _to_response(tenant, assinatura)
        for tenant, assinatura in list_tenants_with_assinaturas(db)
    ]
