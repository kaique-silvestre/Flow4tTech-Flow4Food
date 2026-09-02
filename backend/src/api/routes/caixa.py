from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from src.api.dependencies import get_tenant_db, require_permission
from src.core.limiter import limiter
from src.schemas.caixa import (
    AbrirCaixaRequest,
    CaixaMovimentoResponse,
    CaixaSessaoResponse,
    FecharCaixaRequest,
    MovimentoCaixaRequest,
)
from src.services import audit_service, caixa_service

router = APIRouter(dependencies=[Depends(require_permission("caixa"))])

_WRITE_RATE_LIMIT = "30/minute"
_READ_RATE_LIMIT = "60/minute"


@router.post("/abrir", response_model=CaixaSessaoResponse, status_code=201)
@limiter.limit(_WRITE_RATE_LIMIT)
def abrir_caixa(
    request: Request,
    body: AbrirCaixaRequest,
    background_tasks: BackgroundTasks,
    payload: dict = Depends(require_permission("caixa")),
    db: Session = Depends(get_tenant_db),
) -> CaixaSessaoResponse:
    user_id: int = payload["user_id"]
    result = caixa_service.abrir_caixa(db, body, user_id)
    background_tasks.add_task(
        audit_service.log_background,
        "caixa.sessao.abrir",
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
        entity="CaixaSessao",
        entity_id=result.id,
        after={"valor_abertura": str(body.valor_abertura)},
        impersonated_by=payload.get("impersonated_by"),
    )
    return result


@router.post("/fechar", response_model=CaixaSessaoResponse)
@limiter.limit(_WRITE_RATE_LIMIT)
def fechar_caixa(
    request: Request,
    body: FecharCaixaRequest,
    background_tasks: BackgroundTasks,
    payload: dict = Depends(require_permission("caixa")),
    db: Session = Depends(get_tenant_db),
) -> CaixaSessaoResponse:
    user_id: int = payload["user_id"]
    result = caixa_service.fechar_caixa(db, body, user_id)
    background_tasks.add_task(
        audit_service.log_background,
        "caixa.sessao.fechar",
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
        entity="CaixaSessao",
        entity_id=result.id,
        after={
            "valor_informado": str(body.valor_informado),
            "valor_esperado": str(result.valor_esperado) if result.valor_esperado is not None else None,
            "diferenca": str(result.diferenca) if result.diferenca is not None else None,
        },
        impersonated_by=payload.get("impersonated_by"),
    )
    return result


@router.post("/movimentos", response_model=CaixaMovimentoResponse, status_code=201)
@limiter.limit(_WRITE_RATE_LIMIT)
def registrar_movimento(
    request: Request,
    body: MovimentoCaixaRequest,
    background_tasks: BackgroundTasks,
    payload: dict = Depends(require_permission("caixa")),
    db: Session = Depends(get_tenant_db),
) -> CaixaMovimentoResponse:
    user_id: int = payload["user_id"]
    result = caixa_service.registrar_movimento(db, body, user_id)
    background_tasks.add_task(
        audit_service.log_background,
        f"caixa.movimento.{body.tipo}",
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
        entity="CaixaMovimento",
        entity_id=result.id,
        after={"valor": str(body.valor), "motivo": body.motivo},
        impersonated_by=payload.get("impersonated_by"),
    )
    return result


@router.get("/sessao", response_model=CaixaSessaoResponse)
@limiter.limit(_READ_RATE_LIMIT)
def get_sessao_aberta(
    request: Request,
    db: Session = Depends(get_tenant_db),
) -> CaixaSessaoResponse:
    return caixa_service.get_sessao_aberta(db)
