from datetime import datetime, timezone
from typing import Any, Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from src.api.dependencies import require_platform_admin
from src.core.database import get_platform_db
from src.core.errors import AppError
from src.core.limiter import limiter
from src.repositories import platform_repository, revoked_tokens_repository
from src.services import audit_service, platform_auth_service
from src.services.auth_service import create_access_token, hash_password


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
    response_model=list[TenantListItem],
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def list_tenants(
    status: Optional[str] = None,  # noqa: UP045
    db: Session = Depends(get_platform_db),
) -> list[TenantListItem]:
    rows = platform_repository.list_tenants(db, status_filter=status)
    return [TenantListItem(**r) for r in rows]


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
    response_model=list[CockpitMetricsItem],
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def get_cockpit(
    status: Optional[str] = None,  # noqa: UP045
    db: Session = Depends(get_platform_db),
) -> list[CockpitMetricsItem]:
    rows = platform_repository.get_cockpit_metrics(db, status_filter=status)
    return [CockpitMetricsItem(**r) for r in rows]


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
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
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
    changed_by = payload.get("sub")
    assinatura = platform_repository.update_assinatura_status(
        db, tenant_id, body.status, changed_by=int(changed_by) if changed_by else None
    )
    background_tasks.add_task(
        audit_service.log_background,
        "subscription.update",
        tenant_id=tenant_id,
        after={"status": body.status},
    )
    return {"tenant_id": tenant_id, "status": assinatura.status}


# ─── Additional schemas ────────────────────────────────────────────────────


class PlatformTenantCreate(BaseModel):
    nome_fantasia: str
    cnpj: Optional[str] = None  # noqa: UP045
    endereco: Optional[str] = None  # noqa: UP045
    telefone: Optional[str] = None  # noqa: UP045
    max_users: int = 5
    trial_days: Optional[int] = None  # noqa: UP045


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
    result = platform_repository.create_platform_tenant(
        db,
        nome_fantasia=body.nome_fantasia,
        cnpj=body.cnpj,
        endereco=body.endereco,
        telefone=body.telefone,
        max_users=body.max_users,
        trial_days=trial_days,
    )
    background_tasks.add_task(
        audit_service.log_background,
        "tenant.create",
        tenant_id=result.get("id") if isinstance(result, dict) else None,
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
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
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
    db: Session = Depends(get_platform_db),
) -> TenantDetail:
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
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
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
    changed_by = payload.get("sub")
    assinatura = platform_repository.update_assinatura_status(
        db,
        tenant_id,
        body.status,
        data_vencimento=body.data_vencimento,
        changed_by=int(changed_by) if changed_by else None,
    )
    background_tasks.add_task(
        audit_service.log_background,
        "subscription.update_full",
        tenant_id=tenant_id,
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
    db: Session = Depends(get_platform_db),
) -> PlatformUserResponse:
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
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
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
    db: Session = Depends(get_platform_db),
) -> ProfileResponse:
    row = platform_repository.update_tenant_profile(
        db,
        tenant_id=tenant_id,
        profile_id=profile_id,
        permissions=body.permissions,
        is_active=body.is_active,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
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
    db: Session = Depends(get_platform_db),
) -> list[FeatureItem]:
    rows = platform_repository.upsert_tenant_features(db, tenant_id, body.features)
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
    from datetime import timedelta

    from sqlalchemy import select

    from src.models.system_users import SystemUser
    from src.models.user_permissions import UserPermission

    user = db.execute(
        select(SystemUser).where(SystemUser.id == user_id, SystemUser.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    perms = db.execute(
        select(UserPermission.screen).where(UserPermission.user_id == user_id)
    ).scalars().all()
    if not perms and user.profile_id:
        from src.models.profiles import ProfilePermission
        perms = db.execute(
            select(ProfilePermission.screen).where(ProfilePermission.profile_id == user.profile_id)
        ).scalars().all()

    admin_id = payload.get("sub") or payload.get("admin_id")
    admin_email = payload.get("email", "")
    token_payload: dict[str, Any] = {
        "sub": str(user.id),
        "user_id": user.id,
        "tenant_id": tenant_id,
        "permissions": list(perms),
        "impersonation": True,
        "impersonated_by": admin_id,
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
        impersonated_by=int(admin_id) if admin_id else None,
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
    db: Session = Depends(get_platform_db),
) -> PlatformSettingResponse:
    setting = platform_repository.upsert_setting(db, key, body.value)
    return PlatformSettingResponse(key=setting.key, value=setting.value)
