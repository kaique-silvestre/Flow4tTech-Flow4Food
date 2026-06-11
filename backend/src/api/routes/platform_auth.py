from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.dependencies import require_platform_admin
from src.core.database import get_platform_db
from src.repositories import platform_repository
from src.services import platform_auth_service


class PlatformLoginRequest(BaseModel):
    email: str
    password: str


class PlatformLoginResponse(BaseModel):
    access_token: str


class TenantListItem(BaseModel):
    id: int
    nome_fantasia: str
    cnpj: Optional[str]  # noqa: UP045
    status_tenant: str
    status_assinatura: Optional[str]  # noqa: UP045
    data_vencimento: Optional[datetime]  # noqa: UP045


class TenantUserItem(BaseModel):
    id: int
    name: str
    username: str
    profile_name: str
    last_login: Optional[datetime]  # noqa: UP045
    is_active: bool


class AssinaturaStatusUpdate(BaseModel):
    status: Literal["trial", "ativa", "suspensa", "cancelada"]


# Public router — login endpoint has no auth dependency
_public_router = APIRouter()

# Protected router — all routes require platform admin token
router = APIRouter(dependencies=[Depends(require_platform_admin)])


@_public_router.post(
    "/auth/login",
    response_model=PlatformLoginResponse,
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def platform_login(
    body: PlatformLoginRequest,
    db: Session = Depends(get_platform_db),
) -> PlatformLoginResponse:
    token = platform_auth_service.login(db, body.email, body.password)
    return PlatformLoginResponse(access_token=token)


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


@router.patch(
    "/tenants/{tenant_id}/assinatura",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def update_assinatura(
    tenant_id: int,
    body: AssinaturaStatusUpdate,
    db: Session = Depends(get_platform_db),
) -> dict:
    assinatura = platform_repository.update_assinatura_status(db, tenant_id, body.status)
    return {"tenant_id": tenant_id, "status": assinatura.status}
