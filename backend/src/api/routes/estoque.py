from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.schemas.estoque import (
    BaixaSemVendaRequest,
    MovimentoListResponse,
    SaldoItemResponse,
)
from src.services import estoque_service

router = APIRouter()


@router.get("/saldo", response_model=list[SaldoItemResponse])
def get_saldo(
    categoria_id: Optional[int] = Query(None),
    busca: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> list[SaldoItemResponse]:
    return estoque_service.get_saldo_list(db, categoria_id, busca)  # type: ignore[return-value]


@router.post("/baixa-sem-venda", status_code=status.HTTP_201_CREATED)
def baixa_sem_venda(
    data: BaixaSemVendaRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> dict:
    return estoque_service.baixa_sem_venda(db, data)


@router.get("/movimentos", response_model=MovimentoListResponse)
def list_movimentos(
    item_id: Optional[int] = Query(None),
    tipo: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> MovimentoListResponse:
    return estoque_service.get_historico(db, item_id, tipo, data_inicio, data_fim, pagina, por_pagina)
