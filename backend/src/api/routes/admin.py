import hmac

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.core.database import get_db
from src.core.limiter import limiter
from src.schemas.billing import (
    AssinaturaUpdate,
    PagamentoCreate,
    PagamentoInfo,
    PlanoCreate,
    PlanoInfo,
)
from src.schemas.tenants import AssinaturaInfo, TenantCreate, TenantResponse, TenantUpdate
from src.services import audit_service, billing_service
from src.services.tenant_service import (
    criar_tenant,
    get_all_tenants,
    get_tenant,
    update_existing_tenant,
)

router = APIRouter()

# Mais restritivo que o rate limit de login (5/15minutes) — esta rota controla
# ações de superusuário sobre todos os tenants da plataforma.
_RATE_LIMIT = "3/15minutes"


def require_superadmin(request: Request) -> None:
    """Valida o header Authorization contra SUPERADMIN_TOKEN.

    Chamada explicitamente de dentro do corpo de cada endpoint (não como
    `Depends`) para que a checagem só rode depois que o decorator
    `@limiter.limit` já contou a tentativa — se fosse `Depends`, o FastAPI
    resolveria (e rejeitaria) a credencial antes de o endpoint decorado ser
    chamado, e tentativas com token errado nunca incrementariam o rate limit,
    permitindo brute-force irrestrito do token.
    """
    settings = get_settings()
    if not settings.SUPERADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin não configurado",
        )
    auth_header = request.headers.get("Authorization") or ""
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token or not hmac.compare_digest(
        token, settings.SUPERADMIN_TOKEN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado — token superadmin inválido",
        )


def get_admin_identifier(request: Request) -> str:
    """Identifica manualmente quem usou o SUPERADMIN_TOKEN compartilhado.

    O token estático não carrega identidade própria — este header é a única forma
    de atribuir uma ação de auditoria a uma pessoa. Isso não resolve o problema de
    raiz (o token continua compartilhado), apenas garante que nenhuma ação mutante
    fique anônima no log de auditoria.

    Chamada explicitamente do corpo do endpoint (não `Depends`) e sempre depois
    de `require_superadmin`, pelo mesmo motivo descrito lá: preservar a
    contagem do rate limit e a prioridade do erro de autenticação sobre o de
    payload.
    """
    value = request.headers.get("X-Admin-Identifier")
    if not value or not value.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header X-Admin-Identifier é obrigatório para ações administrativas",
        )
    return value.strip()


def require_superadmin_with_identifier(request: Request) -> str:
    """Combina `require_superadmin` + `get_admin_identifier` na ordem correta.

    Toda rota mutante precisa das duas checagens, sempre nessa ordem; centralizar
    evita repetir as duas chamadas em cada endpoint.
    """
    require_superadmin(request)
    return get_admin_identifier(request)


@router.post("/tenants", response_model=TenantResponse, status_code=201)
@limiter.limit(_RATE_LIMIT)
def create_tenant_endpoint(
    request: Request,
    body: TenantCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> TenantResponse:
    admin_identifier = require_superadmin_with_identifier(request)
    result = criar_tenant(db, body)
    background_tasks.add_task(
        audit_service.log_background,
        "admin.tenant_create",
        entity="tenant",
        entity_id=result.id,
        after={
            "admin_identifier": admin_identifier,
            "nome_fantasia": body.nome_fantasia,
            "admin_email": body.admin_email,
        },
    )
    return result


@router.get("/tenants", response_model=list[TenantResponse])
@limiter.limit(_RATE_LIMIT)
def list_tenants_endpoint(
    request: Request,
    db: Session = Depends(get_db),
) -> list[TenantResponse]:
    require_superadmin(request)
    return get_all_tenants(db)


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
@limiter.limit(_RATE_LIMIT)
def get_tenant_endpoint(
    request: Request,
    tenant_id: int,
    db: Session = Depends(get_db),
) -> TenantResponse:
    require_superadmin(request)
    return get_tenant(db, tenant_id)


@router.patch("/tenants/{tenant_id}", response_model=TenantResponse)
@limiter.limit(_RATE_LIMIT)
def update_tenant_endpoint(
    request: Request,
    tenant_id: int,
    body: TenantUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> TenantResponse:
    admin_identifier = require_superadmin_with_identifier(request)
    result = update_existing_tenant(db, tenant_id, body)
    background_tasks.add_task(
        audit_service.log_background,
        "admin.tenant_update",
        tenant_id=tenant_id,
        entity="tenant",
        entity_id=tenant_id,
        after={
            "admin_identifier": admin_identifier,
            **body.model_dump(exclude_unset=True),
        },
    )
    return result


@router.patch("/tenants/{tenant_id}/subscription", response_model=AssinaturaInfo)
@limiter.limit(_RATE_LIMIT)
def update_subscription_endpoint(
    request: Request,
    tenant_id: int,
    body: AssinaturaUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> AssinaturaInfo:
    admin_identifier = require_superadmin_with_identifier(request)
    result = billing_service.atualizar_assinatura(db, tenant_id, body)
    background_tasks.add_task(
        audit_service.log_background,
        "admin.subscription_update",
        tenant_id=tenant_id,
        entity="assinatura",
        after={
            "admin_identifier": admin_identifier,
            "status": body.status,
            "data_vencimento": str(body.data_vencimento) if body.data_vencimento else None,
        },
    )
    return result


@router.post("/tenants/{tenant_id}/payments", response_model=PagamentoInfo, status_code=201)
@limiter.limit(_RATE_LIMIT)
def register_payment_endpoint(
    request: Request,
    tenant_id: int,
    body: PagamentoCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> PagamentoInfo:
    admin_identifier = require_superadmin_with_identifier(request)
    result = billing_service.registrar_pagamento(db, tenant_id, body)
    background_tasks.add_task(
        audit_service.log_background,
        "admin.payment_register",
        tenant_id=tenant_id,
        entity="pagamento",
        entity_id=result.id,
        after={
            "admin_identifier": admin_identifier,
            "valor": str(body.valor),
            "data_pagamento": str(body.data_pagamento),
        },
    )
    return result


@router.get("/plans", response_model=list[PlanoInfo])
@limiter.limit(_RATE_LIMIT)
def list_plans_endpoint(
    request: Request,
    db: Session = Depends(get_db),
) -> list[PlanoInfo]:
    require_superadmin(request)
    return billing_service.listar_planos(db)


@router.post("/plans", response_model=PlanoInfo, status_code=201)
@limiter.limit(_RATE_LIMIT)
def create_plan_endpoint(
    request: Request,
    body: PlanoCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> PlanoInfo:
    admin_identifier = require_superadmin_with_identifier(request)
    result = billing_service.criar_plano(db, body)
    background_tasks.add_task(
        audit_service.log_background,
        "admin.plan_create",
        entity="plano",
        entity_id=result.id,
        after={
            "admin_identifier": admin_identifier,
            "nome": body.nome,
            "preco_mensal": str(body.preco_mensal),
        },
    )
    return result
