import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.schemas.relatorio_schemas import (
    FechamentoCaixaResponse,
    HistoricoResponse,
    VendasDoDiaResponse,
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
