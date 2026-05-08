import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.schemas.relatorio_schemas import (
    CMVPorProdutoResponse,
    DREResponse,
    FechamentoCaixaResponse,
    HistoricoResponse,
    PerdasCortesiasResponse,
    VendasDoDiaResponse,
    VendasPorGarcomResponse,
)
from src.services import relatorio_service

router = APIRouter()


@router.get("/vendas-do-dia", response_model=VendasDoDiaResponse)
def vendas_do_dia(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> VendasDoDiaResponse:
    return relatorio_service.vendas_do_dia(db)


@router.get("/historico-comandas", response_model=HistoricoResponse)
def historico_comandas(
    data_inicio: datetime.date = Query(...),
    data_fim: datetime.date = Query(...),
    garcom_id: Optional[int] = Query(None),
    busca: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> HistoricoResponse:
    return relatorio_service.historico_comandas(db, data_inicio, data_fim, garcom_id, busca)


@router.get("/fechamento-caixa", response_model=FechamentoCaixaResponse)
def fechamento_caixa(
    data: datetime.date = Query(...),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> FechamentoCaixaResponse:
    return relatorio_service.fechamento_caixa(db, data)


@router.get("/dre", response_model=DREResponse)
def dre(
    mes: str = Query(..., description="Formato YYYY-MM"),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> DREResponse:
    return relatorio_service.dre(db, mes)


@router.get("/cmv-por-produto", response_model=CMVPorProdutoResponse)
def cmv_por_produto(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> CMVPorProdutoResponse:
    return relatorio_service.cmv_por_produto(db)


@router.get("/perdas-cortesias", response_model=PerdasCortesiasResponse)
def perdas_cortesias(
    data_inicio: datetime.date = Query(...),
    data_fim: datetime.date = Query(...),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> PerdasCortesiasResponse:
    return relatorio_service.perdas_cortesias(db, data_inicio, data_fim)


@router.get("/vendas-por-garcom", response_model=VendasPorGarcomResponse)
def vendas_por_garcom(
    data_inicio: datetime.date = Query(...),
    data_fim: datetime.date = Query(...),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> VendasPorGarcomResponse:
    return relatorio_service.vendas_por_garcom(db, data_inicio, data_fim)
