from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.database import get_db
from src.schemas.billing import (
    AssinaturaUpdate,
    PagamentoCreate,
    PagamentoInfo,
    PlanoCreate,
    PlanoInfo,
)
from src.schemas.tenants import AssinaturaInfo, TenantCreate, TenantResponse, TenantUpdate
from src.services import billing_service
from src.services.tenant_service import (
    criar_tenant,
    get_all_tenants,
    get_tenant,
    update_existing_tenant,
)

router = APIRouter()

_bearer = HTTPBearer(auto_error=False)


def require_superadmin(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_bearer)],
) -> None:
    settings = get_settings()
    if not settings.SUPERADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin não configurado",
        )
    if credentials is None or credentials.credentials != settings.SUPERADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado — token superadmin inválido",
        )


@router.post("/tenants", response_model=TenantResponse, status_code=201)
def create_tenant_endpoint(
    body: TenantCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_superadmin),
) -> TenantResponse:
    return criar_tenant(db, body)


@router.get("/tenants", response_model=list[TenantResponse])
def list_tenants_endpoint(
    db: Session = Depends(get_db),
    _: None = Depends(require_superadmin),
) -> list[TenantResponse]:
    return get_all_tenants(db)


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
def get_tenant_endpoint(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_superadmin),
) -> TenantResponse:
    return get_tenant(db, tenant_id)


@router.patch("/tenants/{tenant_id}", response_model=TenantResponse)
def update_tenant_endpoint(
    tenant_id: int,
    body: TenantUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_superadmin),
) -> TenantResponse:
    return update_existing_tenant(db, tenant_id, body)


@router.patch("/tenants/{tenant_id}/subscription", response_model=AssinaturaInfo)
def update_subscription_endpoint(
    tenant_id: int,
    body: AssinaturaUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_superadmin),
) -> AssinaturaInfo:
    return billing_service.atualizar_assinatura(db, tenant_id, body)


@router.post("/tenants/{tenant_id}/payments", response_model=PagamentoInfo, status_code=201)
def register_payment_endpoint(
    tenant_id: int,
    body: PagamentoCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_superadmin),
) -> PagamentoInfo:
    return billing_service.registrar_pagamento(db, tenant_id, body)


@router.get("/plans", response_model=list[PlanoInfo])
def list_plans_endpoint(
    db: Session = Depends(get_db),
    _: None = Depends(require_superadmin),
) -> list[PlanoInfo]:
    return billing_service.listar_planos(db)


@router.post("/plans", response_model=PlanoInfo, status_code=201)
def create_plan_endpoint(
    body: PlanoCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_superadmin),
) -> PlanoInfo:
    return billing_service.criar_plano(db, body)
