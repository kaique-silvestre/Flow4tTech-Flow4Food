from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, status
from sqlalchemy.orm import Session

from src.api.dependencies import (
    get_current_user,
    get_tenant_db,
    require_feature,
    require_permission,
)
from src.core.limiter import limiter
from src.schemas.estoque import (
    BaixaSemVendaRequest,
    InsumoCriticoResponse,
    MovimentoListResponse,
    MovimentoProdutoListResponse,
    SaldoPageResponse,
)
from src.services import audit_service, estoque_service

router = APIRouter(dependencies=[Depends(require_feature("estoque")), Depends(require_permission("estoque"))])

_BAIXA_RATE_LIMIT = "30/minute"


@router.get("/criticos", response_model=list[InsumoCriticoResponse])
def get_criticos(
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> list[InsumoCriticoResponse]:
    return estoque_service.get_insumos_criticos(db)  # type: ignore[return-value]


@router.get("/saldo", response_model=SaldoPageResponse)
def get_saldo(
    categoria_id: Optional[int] = Query(None),
    busca: Optional[str] = Query(None),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(500, ge=1, le=500),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> SaldoPageResponse:
    return estoque_service.get_saldo_list(db, categoria_id, busca, pagina, por_pagina)  # type: ignore[return-value]


@router.post("/baixa-sem-venda", status_code=status.HTTP_201_CREATED)
@limiter.limit(_BAIXA_RATE_LIMIT)
def baixa_sem_venda(
    request: Request,
    data: BaixaSemVendaRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(get_current_user),
) -> dict:
    result = estoque_service.baixa_sem_venda(
        db,
        data,
        payload.get("user_id"),
        payload.get("tenant_id"),
    )
    background_tasks.add_task(
        audit_service.log_background,
        "estoque.baixa_sem_venda",
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
        entity="MovimentoEstoque",
        entity_id=result["movimento"].id,
        after={
            "insumo_id": data.item_id,
            "quantidade": str(data.quantidade),
            "motivo": data.motivo.value,
        },
        impersonated_by=payload.get("impersonated_by"),
    )
    return result


@router.get("/movimentos", response_model=MovimentoListResponse)
def list_movimentos(
    item_id: Optional[int] = Query(None),
    tipo: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> MovimentoListResponse:
    return estoque_service.get_historico(db, item_id, tipo, data_inicio, data_fim, pagina, por_pagina)


@router.get("/movimentos-produtos", response_model=MovimentoProdutoListResponse)
def list_movimentos_produtos(
    produto_id: Optional[int] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> MovimentoProdutoListResponse:
    return estoque_service.get_historico_produtos(db, produto_id, data_inicio, data_fim, pagina, por_pagina)
