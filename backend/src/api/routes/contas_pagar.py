from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db, require_permission
from src.schemas.contas_pagar_schemas import (
    ContaPagarResponse,
    ContasPagarPageResponse,
    ContasPagarResumoResponse,
    NotificacaoResponse,
    PagarContaRequest,
)
from src.services import contas_pagar_service

router = APIRouter(dependencies=[Depends(require_permission("compras"))])


@router.get("", response_model=ContasPagarPageResponse)
def list_contas(
    status: Optional[str] = Query(None),
    data_vencimento_inicio: Optional[str] = Query(None),
    data_vencimento_fim: Optional[str] = Query(None),
    fornecedor_id: Optional[int] = Query(None),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ContasPagarPageResponse:
    return contas_pagar_service.list_contas(
        db, status, data_vencimento_inicio, data_vencimento_fim, fornecedor_id, pagina, por_pagina
    )


@router.get("/resumo", response_model=ContasPagarResumoResponse)
def resumo(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ContasPagarResumoResponse:
    return contas_pagar_service.resumo(db)


@router.post("/{conta_id}/pagar", response_model=ContaPagarResponse)
def pagar_conta(
    conta_id: int,
    data: PagarContaRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ContaPagarResponse:
    return contas_pagar_service.pagar_conta(db, conta_id, data)


@router.get("/notificacoes", response_model=list[NotificacaoResponse])
def list_notificacoes(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> list[NotificacaoResponse]:
    return contas_pagar_service.list_notificacoes(db)


@router.post("/notificacoes/{notificacao_id}/marcar-lida")
def marcar_lida(
    notificacao_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> dict:
    contas_pagar_service.marcar_notificacao_lida(db, notificacao_id)
    return {"ok": True}
