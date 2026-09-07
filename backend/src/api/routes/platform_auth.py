from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.dependencies import require_platform_admin
from src.core.database import get_platform_db
from src.core.errors import AppError, ErrorCode
from src.core.limiter import limiter
from src.core.logging import get_logger
from src.models.system_users import SystemUser
from src.repositories import platform_repository, revoked_tokens_repository
from src.schemas.tenants import TenantCreate
from src.services import audit_service, platform_auth_service, platform_service
from src.services.auth_service import create_access_token, hash_password
from src.services.tenant_service import criar_tenant as provision_tenant

logger = get_logger(__name__)


class PlatformLoginRequest(BaseModel):
    email: str
    password: str


class PlatformLoginResponse(BaseModel):
    access_token: str


class TenantListItem(BaseModel):
    id: int
    nome_fantasia: str
    cnpj: Optional[str]  # noqa: UP045
    max_users: int = 0
    status_tenant: str
    status_assinatura: Optional[str]  # noqa: UP045
    data_vencimento: Optional[datetime]  # noqa: UP045
    qtd_usuarios: int = 0


class TenantPage(BaseModel):
    items: list[TenantListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class TenantUserItem(BaseModel):
    id: int
    name: str
    username: str
    email: Optional[str]  # noqa: UP045
    profile_id: Optional[int]  # noqa: UP045
    profile_name: Optional[str]  # noqa: UP045
    last_login: Optional[datetime]  # noqa: UP045
    is_active: bool


class AssinaturaStatusUpdate(BaseModel):
    status: Literal["trial", "ativa", "suspensa", "cancelada"]


class CockpitMetricsItem(BaseModel):
    id: int
    nome_fantasia: str
    cnpj: Optional[str]  # noqa: UP045
    status_tenant: str
    status_assinatura: Optional[str]  # noqa: UP045
    dias_cliente: int
    ultimo_login: Optional[datetime]  # noqa: UP045
    comandas_mes: int
    faturamento_mes: float
    usuarios_ativos_30d: int
    compras_mes: int


class CockpitPage(BaseModel):
    items: list[CockpitMetricsItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# Public router — login endpoint has no auth dependency
_public_router = APIRouter()

# Protected router — all routes require platform admin token
router = APIRouter(dependencies=[Depends(require_platform_admin)])

_LOGIN_RATE_LIMIT = "5/15minutes"
# Admin write actions (tenant/user provisioning, subscription changes,
# impersonation) are more sensitive than routine reads — throttle harder.
_ADMIN_WRITE_RATE_LIMIT = "10/minute"


@_public_router.post(
    "/auth/login",
    response_model=PlatformLoginResponse,
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
@limiter.limit(_LOGIN_RATE_LIMIT)
def platform_login(
    request: Request,
    body: PlatformLoginRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_platform_db),
) -> PlatformLoginResponse:
    try:
        token = platform_auth_service.login(db, body.email, body.password)
    except AppError:
        background_tasks.add_task(
            audit_service.log_background,
            "platform.login_failed",
            after={"email": body.email},
        )
        raise
    platform_admin_id = _decode_platform_admin_id(token)
    background_tasks.add_task(
        audit_service.log_background,
        "platform.login_success",
        user_id=platform_admin_id,
    )
    return PlatformLoginResponse(access_token=token)


def _decode_platform_admin_id(access_token: str) -> Optional[int]:
    import jwt as _jwt

    from src.core.config import get_settings

    try:
        settings = get_settings()
        payload = _jwt.decode(
            access_token, settings.JWT_SECRET, algorithms=["HS256"], options={"require": ["exp"]}
        )
        return payload.get("platform_admin_id")
    except Exception:
        logger.warning("platform_admin_id_decode_failed", exc_info=True)
        return None


def _platform_actor_id(payload: dict) -> Optional[int]:
    """Return the authenticated platform administrator id for audit records.

    Older tokens used ``admin_id`` while current platform login tokens use
    ``platform_admin_id``.  Keeping the compatibility fallback means every
    protected mutation retains an accountable actor during the transition.
    """
    actor_id = payload.get("platform_admin_id") or payload.get("admin_id") or payload.get("sub")
    try:
        return int(actor_id) if actor_id is not None else None
    except (TypeError, ValueError):
        return None


@router.post(
    "/auth/logout",
    status_code=204,
    tags=["platform"],
)
def platform_logout(
    background_tasks: BackgroundTasks,
    payload: dict = Depends(require_platform_admin),
    db: Session = Depends(get_platform_db),
) -> None:
    jti = payload.get("jti")
    exp_ts = payload.get("exp")
    if jti and exp_ts:
        expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
        revoked_tokens_repository.revoke(db, jti, expires_at)
    background_tasks.add_task(
        audit_service.log_background,
        "platform.logout",
        user_id=payload.get("platform_admin_id"),
    )
    return None


@router.get(
    "/tenants",
    response_model=TenantPage,
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def list_tenants(
    status: Optional[str] = None,  # noqa: UP045
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_platform_db),
) -> TenantPage:
    result = platform_repository.list_tenants(
        db, status_filter=status, page=page, page_size=page_size
    )
    return TenantPage(**result)


@router.get(
    "/tenants/{tenant_id}/users",
    response_model=list[TenantUserItem],
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def get_tenant_users(
    tenant_id: int,
    db: Session = Depends(get_platform_db),
) -> list[TenantUserItem]:
    rows = platform_repository.get_tenant_users(db, tenant_id)
    return [TenantUserItem(**r) for r in rows]


@router.get(
    "/cockpit",
    response_model=CockpitPage,
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def get_cockpit(
    status: Optional[str] = None,  # noqa: UP045
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_platform_db),
) -> CockpitPage:
    result = platform_repository.get_cockpit_metrics(
        db, status_filter=status, page=page, page_size=page_size
    )
    return CockpitPage(**result)


@router.get(
    "/tenants/{tenant_id}/cockpit",
    response_model=CockpitMetricsItem,
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def get_tenant_cockpit(
    tenant_id: int,
    db: Session = Depends(get_platform_db),
) -> CockpitMetricsItem:
    row = platform_repository.get_tenant_cockpit_metrics(db, tenant_id)
    if row is None:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Tenant não encontrado", http_status=404)
    return CockpitMetricsItem(**row)


@router.patch(
    "/tenants/{tenant_id}/assinatura",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
@limiter.limit(_ADMIN_WRITE_RATE_LIMIT)
def update_assinatura(
    request: Request,
    tenant_id: int,
    body: AssinaturaStatusUpdate,
    background_tasks: BackgroundTasks,
    payload: dict = Depends(require_platform_admin),
    db: Session = Depends(get_platform_db),
) -> dict:
    actor_id = _platform_actor_id(payload)
    assinatura = platform_repository.update_assinatura_status(
        db, tenant_id, body.status, changed_by=actor_id
    )
    background_tasks.add_task(
        audit_service.log_background,
        "subscription.update",
        tenant_id=tenant_id,
        user_id=actor_id,
        entity="Assinatura",
        entity_id=assinatura.id,
        after={"status": body.status},
    )
    return {"tenant_id": tenant_id, "status": assinatura.status}


# ─── Additional schemas ────────────────────────────────────────────────────


class PlatformTenantCreate(BaseModel):
    nome_fantasia: str = Field(..., min_length=1, max_length=200)
    cnpj: Optional[str] = None  # noqa: UP045
    endereco: Optional[str] = None  # noqa: UP045
    telefone: Optional[str] = None  # noqa: UP045
    max_users: int = 5
    trial_days: Optional[int] = None  # noqa: UP045
    admin_name: str = Field(..., min_length=1, max_length=200)
    admin_username: str = Field(..., min_length=3, max_length=100)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=6, max_length=72)


class TenantDetail(BaseModel):
    id: int
    nome_fantasia: str
    cnpj: Optional[str]  # noqa: UP045
    endereco: Optional[str]  # noqa: UP045
    telefone: Optional[str]  # noqa: UP045
    status: str
    max_users: int
    qtd_usuarios: int
    created_at: datetime
    status_assinatura: Optional[str]  # noqa: UP045
    data_vencimento: Optional[datetime]  # noqa: UP045
    data_inicio: Optional[datetime]  # noqa: UP045


class TenantUpdate(BaseModel):
    nome_fantasia: Optional[str] = None  # noqa: UP045
    cnpj: Optional[str] = None  # noqa: UP045
    endereco: Optional[str] = None  # noqa: UP045
    telefone: Optional[str] = None  # noqa: UP045
    max_users: Optional[int] = None  # noqa: UP045


class AssinaturaFullUpdate(BaseModel):
    status: Literal["trial", "ativa", "suspensa", "cancelada"]
    data_vencimento: Optional[datetime] = None  # noqa: UP045


class AssinaturaHistoryItem(BaseModel):
    id: int
    from_status: Optional[str]  # noqa: UP045
    to_status: str
    changed_by: Optional[int]  # noqa: UP045
    changed_by_name: Optional[str] = None  # noqa: UP045
    created_at: datetime


class PlatformUserCreate(BaseModel):
    name: str
    username: str
    email: Optional[str] = None  # noqa: UP045
    password: str
    profile_id: Optional[int] = None  # noqa: UP045
    is_active: bool = True

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Senha deve ter no mínimo 6 caracteres")
        return v


class PlatformUserUpdate(BaseModel):
    name: Optional[str] = None  # noqa: UP045
    username: Optional[str] = None  # noqa: UP045
    email: Optional[str] = None  # noqa: UP045
    password: Optional[str] = None  # noqa: UP045
    profile_id: Optional[int] = None  # noqa: UP045
    is_active: Optional[bool] = None  # noqa: UP045

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: Optional[str]) -> Optional[str]:  # noqa: UP045
        if v is not None and len(v) < 6:
            raise ValueError("Senha deve ter no mínimo 6 caracteres")
        return v


class PlatformUserResponse(BaseModel):
    id: int
    name: str
    username: str
    email: Optional[str]  # noqa: UP045
    profile_id: Optional[int]  # noqa: UP045
    profile_name: Optional[str]  # noqa: UP045
    is_active: bool
    last_login: Optional[datetime]  # noqa: UP045


class ProfilePermissionsUpdate(BaseModel):
    permissions: Optional[list[str]] = None  # noqa: UP045
    is_active: Optional[bool] = None  # noqa: UP045


class ProfileResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]  # noqa: UP045
    is_active: bool
    permissions: list[str]
    user_count: int


class FeaturesUpdate(BaseModel):
    features: dict[str, bool]


class FeatureItem(BaseModel):
    feature: str
    enabled: bool


class PlatformSettingResponse(BaseModel):
    key: str
    value: str


class PlatformSettingUpdate(BaseModel):
    value: str


class ImpersonateResponse(BaseModel):
    access_token: str


# ─── New endpoints ─────────────────────────────────────────────────────────


@router.post(
    "/tenants",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    tags=["platform"],
)
@limiter.limit(_ADMIN_WRITE_RATE_LIMIT)
def create_tenant(
    request: Request,
    body: PlatformTenantCreate,
    background_tasks: BackgroundTasks,
    payload: dict = Depends(require_platform_admin),
    db: Session = Depends(get_platform_db),
) -> dict:
    trial_days = body.trial_days
    if trial_days is None:
        setting = platform_repository.get_setting(db, "trial_duration_days")
        trial_days = int(setting) if setting else 14
    provisioned = provision_tenant(
        db,
        TenantCreate(
            nome_fantasia=body.nome_fantasia,
            cnpj=body.cnpj,
            admin_name=body.admin_name,
            admin_username=body.admin_username,
            admin_email=body.admin_email,
            admin_password=body.admin_password,
        ),
        endereco=body.endereco,
        telefone=body.telefone,
        max_users=body.max_users,
        trial_days=trial_days,
    )
    result = {
        "id": provisioned.id,
        "nome_fantasia": provisioned.nome_fantasia,
        "cnpj": provisioned.cnpj,
        "status_tenant": provisioned.status,
        "status_assinatura": provisioned.assinatura.status if provisioned.assinatura else None,
        "data_vencimento": provisioned.assinatura.data_vencimento if provisioned.assinatura else None,
        "max_users": body.max_users,
        "qtd_usuarios": 1,
    }
    background_tasks.add_task(
        audit_service.log_background,
        "tenant.create",
        tenant_id=provisioned.id,
        user_id=_platform_actor_id(payload),
        entity="Tenant",
        entity_id=provisioned.id,
        after={"nome_fantasia": body.nome_fantasia},
    )
    return result


@router.get(
    "/tenants/{tenant_id}",
    response_model=TenantDetail,
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def get_tenant_detail(
    tenant_id: int,
    db: Session = Depends(get_platform_db),
) -> TenantDetail:
    detail = platform_repository.get_tenant_detail(db, tenant_id)
    if detail is None:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Tenant não encontrado", http_status=404)
    return TenantDetail(**detail)


@router.patch(
    "/tenants/{tenant_id}",
    response_model=TenantDetail,
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def update_tenant(
    tenant_id: int,
    body: TenantUpdate,
    background_tasks: BackgroundTasks,
    payload: dict = Depends(require_platform_admin),
    db: Session = Depends(get_platform_db),
) -> TenantDetail:
    before = platform_repository.get_tenant_detail(db, tenant_id)
    detail = platform_repository.update_tenant(
        db,
        tenant_id=tenant_id,
        nome_fantasia=body.nome_fantasia,
        cnpj=body.cnpj,
        endereco=body.endereco,
        telefone=body.telefone,
        max_users=body.max_users,
    )
    if detail is None:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Tenant não encontrado", http_status=404)
    platform_service.audited_field_update(
        background_tasks,
        action="platform.tenant.update",
        tenant_id=tenant_id,
        actor_id=_platform_actor_id(payload),
        entity="Tenant",
        entity_id=tenant_id,
        before_row=before or {},
        after_row=detail,
        fields=("nome_fantasia", "cnpj", "endereco", "telefone", "max_users"),
    )
    return TenantDetail(**detail)


@router.patch(
    "/tenants/{tenant_id}/assinatura/full",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
@limiter.limit(_ADMIN_WRITE_RATE_LIMIT)
def update_assinatura_full(
    request: Request,
    tenant_id: int,
    body: AssinaturaFullUpdate,
    background_tasks: BackgroundTasks,
    payload: dict = Depends(require_platform_admin),
    db: Session = Depends(get_platform_db),
) -> dict:
    actor_id = _platform_actor_id(payload)
    assinatura = platform_repository.update_assinatura_status(
        db,
        tenant_id,
        body.status,
        data_vencimento=body.data_vencimento,
        changed_by=actor_id,
    )
    background_tasks.add_task(
        audit_service.log_background,
        "subscription.update_full",
        tenant_id=tenant_id,
        user_id=actor_id,
        entity="Assinatura",
        entity_id=assinatura.id,
        after={"status": body.status, "data_vencimento": body.data_vencimento.isoformat() if body.data_vencimento else None},
    )
    return {"tenant_id": tenant_id, "status": assinatura.status, "data_vencimento": assinatura.data_vencimento}


@router.get(
    "/tenants/{tenant_id}/assinatura/historico",
    response_model=list[AssinaturaHistoryItem],
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def get_assinatura_history(
    tenant_id: int,
    db: Session = Depends(get_platform_db),
) -> list[AssinaturaHistoryItem]:
    rows = platform_repository.get_assinatura_history(db, tenant_id)
    return [AssinaturaHistoryItem(**r) for r in rows]


@router.post(
    "/tenants/{tenant_id}/users",
    response_model=PlatformUserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["platform"],
)
@limiter.limit(_ADMIN_WRITE_RATE_LIMIT)
def create_platform_user(
    request: Request,
    tenant_id: int,
    body: PlatformUserCreate,
    background_tasks: BackgroundTasks,
    payload: dict = Depends(require_platform_admin),
    db: Session = Depends(get_platform_db),
) -> PlatformUserResponse:
    user = platform_repository.create_tenant_user(
        db,
        tenant_id=tenant_id,
        name=body.name,
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        profile_id=body.profile_id,
        is_active=body.is_active,
    )
    background_tasks.add_task(
        audit_service.log_background,
        "platform.tenant_user.create",
        tenant_id=tenant_id,
        user_id=_platform_actor_id(payload),
        entity="SystemUser",
        entity_id=user["id"],
        after={
            "username": user["username"],
            "profile_id": user["profile_id"],
            "is_active": user["is_active"],
        },
    )
    return PlatformUserResponse(**user)


@router.patch(
    "/tenants/{tenant_id}/users/{user_id}",
    response_model=PlatformUserResponse,
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
@limiter.limit(_ADMIN_WRITE_RATE_LIMIT)
def update_platform_user(
    request: Request,
    tenant_id: int,
    user_id: int,
    body: PlatformUserUpdate,
    background_tasks: BackgroundTasks,
    payload: dict = Depends(require_platform_admin),
    db: Session = Depends(get_platform_db),
) -> PlatformUserResponse:
    before = next(
        (user for user in platform_repository.get_tenant_users(db, tenant_id) if user["id"] == user_id),
        None,
    )
    pw_hash = hash_password(body.password) if body.password else None
    user = platform_repository.update_tenant_user(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        name=body.name,
        username=body.username,
        email=body.email,
        password_hash=pw_hash,
        profile_id=body.profile_id,
        is_active=body.is_active,
    )
    if user is None:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Usuário não encontrado", http_status=404)
    platform_service.audited_field_update(
        background_tasks,
        action="platform.tenant_user.update",
        tenant_id=tenant_id,
        actor_id=_platform_actor_id(payload),
        entity="SystemUser",
        entity_id=user_id,
        before_row=before or {},
        after_row=user,
        fields=("username", "profile_id", "is_active"),
        extra_after={"password_changed": body.password is not None},
    )
    return PlatformUserResponse(**user)


@router.get(
    "/tenants/{tenant_id}/profiles",
    response_model=list[ProfileResponse],
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def get_tenant_profiles(
    tenant_id: int,
    db: Session = Depends(get_platform_db),
) -> list[ProfileResponse]:
    rows = platform_repository.get_tenant_profiles(db, tenant_id)
    return [ProfileResponse(**r) for r in rows]


@router.patch(
    "/tenants/{tenant_id}/profiles/{profile_id}",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def update_tenant_profile(
    tenant_id: int,
    profile_id: int,
    body: ProfilePermissionsUpdate,
    background_tasks: BackgroundTasks,
    payload: dict = Depends(require_platform_admin),
    db: Session = Depends(get_platform_db),
) -> ProfileResponse:
    before = next(
        (profile for profile in platform_repository.get_tenant_profiles(db, tenant_id) if profile["id"] == profile_id),
        None,
    )
    row = platform_repository.update_tenant_profile(
        db,
        tenant_id=tenant_id,
        profile_id=profile_id,
        permissions=body.permissions,
        is_active=body.is_active,
    )
    if row is None:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Perfil não encontrado", http_status=404)
    background_tasks.add_task(
        audit_service.log_background,
        "platform.profile.update",
        tenant_id=tenant_id,
        user_id=_platform_actor_id(payload),
        entity="Profile",
        entity_id=profile_id,
        before=(
            {"permissions": before["permissions"], "is_active": before["is_active"]}
            if before is not None
            else None
        ),
        after={"permissions": row["permissions"], "is_active": row["is_active"]},
    )
    return ProfileResponse(**row)


@router.get(
    "/tenants/{tenant_id}/features",
    response_model=list[FeatureItem],
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def get_tenant_features(
    tenant_id: int,
    db: Session = Depends(get_platform_db),
) -> list[FeatureItem]:
    rows = platform_repository.get_tenant_features(db, tenant_id)
    return [FeatureItem(**r) for r in rows]


@router.put(
    "/tenants/{tenant_id}/features",
    response_model=list[FeatureItem],
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def upsert_tenant_features(
    tenant_id: int,
    body: FeaturesUpdate,
    background_tasks: BackgroundTasks,
    payload: dict = Depends(require_platform_admin),
    db: Session = Depends(get_platform_db),
) -> list[FeatureItem]:
    before = {
        row["feature"]: row["enabled"]
        for row in platform_repository.get_tenant_features(db, tenant_id)
    }
    rows = platform_repository.upsert_tenant_features(db, tenant_id, body.features)
    background_tasks.add_task(
        audit_service.log_background,
        "platform.tenant_features.update",
        tenant_id=tenant_id,
        user_id=_platform_actor_id(payload),
        entity="TenantFeature",
        entity_id=None,
        before=before,
        after=body.features,
    )
    return [FeatureItem(**r) for r in rows]


@router.post(
    "/tenants/{tenant_id}/users/{user_id}/impersonate",
    response_model=ImpersonateResponse,
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
@limiter.limit(_ADMIN_WRITE_RATE_LIMIT)
def impersonate_user(
    request: Request,
    tenant_id: int,
    user_id: int,
    background_tasks: BackgroundTasks,
    payload: dict = Depends(require_platform_admin),
    db: Session = Depends(get_platform_db),
) -> ImpersonateResponse:
    user = db.execute(
        select(SystemUser).where(SystemUser.id == user_id, SystemUser.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if user is None:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Usuário não encontrado", http_status=404)

    perms = platform_service.resolve_impersonation_permissions(db, user)

    actor_id = _platform_actor_id(payload)
    admin_email = payload.get("email", "")
    token_payload: dict[str, Any] = {
        "sub": str(user.id),
        "user_id": user.id,
        "tenant_id": tenant_id,
        "permissions": perms,
        "impersonation": True,
        "impersonated_by": actor_id,
        "impersonated_by_email": admin_email,
    }
    token = create_access_token(token_payload, expires_delta=timedelta(hours=2))
    background_tasks.add_task(
        audit_service.log_background,
        "impersonation.start",
        tenant_id=tenant_id,
        user_id=user_id,
        entity="SystemUser",
        entity_id=user_id,
        impersonated_by=actor_id,
    )
    return ImpersonateResponse(access_token=token)


@router.get(
    "/settings",
    response_model=list[PlatformSettingResponse],
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def list_settings(
    db: Session = Depends(get_platform_db),
) -> list[PlatformSettingResponse]:
    rows = platform_repository.list_settings(db)
    return [PlatformSettingResponse(key=r.key, value=r.value) for r in rows]


@router.patch(
    "/settings/{key}",
    response_model=PlatformSettingResponse,
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def update_setting(
    key: str,
    body: PlatformSettingUpdate,
    background_tasks: BackgroundTasks,
    payload: dict = Depends(require_platform_admin),
    db: Session = Depends(get_platform_db),
) -> PlatformSettingResponse:
    before = platform_repository.get_setting(db, key)
    setting = platform_repository.upsert_setting(db, key, body.value)
    background_tasks.add_task(
        audit_service.log_background,
        "platform.setting.update",
        user_id=_platform_actor_id(payload),
        entity="PlatformSettings",
        entity_id=None,
        before={"value": before} if before is not None else None,
        after={"key": setting.key, "value": setting.value},
    )
    return PlatformSettingResponse(key=setting.key, value=setting.value)
