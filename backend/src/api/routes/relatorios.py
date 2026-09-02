import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from src.api.dependencies import (
    get_current_user,
    get_tenant_db,
    require_feature,
    require_permission,
)
from src.core.limiter import limiter
from src.schemas.relatorio_schemas import (
    CMVPorProdutoResponse,
    DREResponse,
    FechamentoCaixaResponse,
    HistoricoResponse,
    PerdasCortesiasResponse,
    PicoVendasHorarioResponse,
    ProdutosMaisVendidosResponse,
    VendasDoDiaResponse,
    VendasPorGarcomResponse,
    VendasPorProdutoResponse,
)
from src.services import relatorio_service

router = APIRouter(dependencies=[Depends(require_feature("relatorios")), Depends(require_permission("relatorios"))])

_REPORT_RATE_LIMIT = "60/minute"


@router.get("/vendas-do-dia", response_model=VendasDoDiaResponse)
@limiter.limit(_REPORT_RATE_LIMIT)
def vendas_do_dia(
    request: Request,
    data: Optional[datetime.date] = Query(None),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> VendasDoDiaResponse:
    return relatorio_service.vendas_do_dia(db, data)


@router.get("/historico-comandas", response_model=HistoricoResponse)
@limiter.limit(_REPORT_RATE_LIMIT)
def historico_comandas(
    request: Request,
    data_inicio: datetime.date = Query(...),
    data_fim: datetime.date = Query(...),
    garcom_id: Optional[int] = Query(None),
    busca: Optional[str] = Query(None),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> HistoricoResponse:
    return relatorio_service.historico_comandas(db, data_inicio, data_fim, garcom_id, busca)


@router.get("/fechamento-caixa", response_model=FechamentoCaixaResponse)
@limiter.limit(_REPORT_RATE_LIMIT)
def fechamento_caixa(
    request: Request,
    data: datetime.date = Query(...),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> FechamentoCaixaResponse:
    return relatorio_service.fechamento_caixa(db, data)


@router.get("/dre", response_model=DREResponse)
@limiter.limit(_REPORT_RATE_LIMIT)
def dre(
    request: Request,
    mes: str = Query(..., description="Formato YYYY-MM"),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> DREResponse:
    return relatorio_service.dre(db, mes)


@router.get("/cmv-por-produto", response_model=CMVPorProdutoResponse)
@limiter.limit(_REPORT_RATE_LIMIT)
def cmv_por_produto(
    request: Request,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> CMVPorProdutoResponse:
    return relatorio_service.cmv_por_produto(db)


@router.get("/perdas-cortesias", response_model=PerdasCortesiasResponse)
@limiter.limit(_REPORT_RATE_LIMIT)
def perdas_cortesias(
    request: Request,
    data_inicio: datetime.date = Query(...),
    data_fim: datetime.date = Query(...),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> PerdasCortesiasResponse:
    return relatorio_service.perdas_cortesias(db, data_inicio, data_fim)


@router.get("/vendas-por-garcom", response_model=VendasPorGarcomResponse)
@limiter.limit(_REPORT_RATE_LIMIT)
def vendas_por_garcom(
    request: Request,
    data_inicio: datetime.date = Query(...),
    data_fim: datetime.date = Query(...),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> VendasPorGarcomResponse:
    return relatorio_service.vendas_por_garcom(db, data_inicio, data_fim)


@router.get("/produtos-mais-vendidos", response_model=ProdutosMaisVendidosResponse)
@limiter.limit(_REPORT_RATE_LIMIT)
def produtos_mais_vendidos(
    request: Request,
    data_inicio: datetime.date = Query(...),
    data_fim: datetime.date = Query(...),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> ProdutosMaisVendidosResponse:
    return relatorio_service.produtos_mais_vendidos(db, data_inicio, data_fim)


@router.get("/pico-vendas-horario", response_model=PicoVendasHorarioResponse)
@limiter.limit(_REPORT_RATE_LIMIT)
def pico_vendas_horario(
    request: Request,
    data_inicio: datetime.date = Query(...),
    data_fim: datetime.date = Query(...),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> PicoVendasHorarioResponse:
    return relatorio_service.pico_vendas_horario(db, data_inicio, data_fim)


@router.get("/vendas-por-produto", response_model=VendasPorProdutoResponse)
@limiter.limit(_REPORT_RATE_LIMIT)
def vendas_por_produto(
    request: Request,
    data_inicio: datetime.date = Query(...),
    data_fim: datetime.date = Query(...),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> VendasPorProdutoResponse:
    return relatorio_service.vendas_por_produto(db, data_inicio, data_fim)
