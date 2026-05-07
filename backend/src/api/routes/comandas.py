from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.schemas.comandas import (
    CancelarItemRequest,
    ComandaCreateRequest,
    ComandaResponse,
    EditarItemRequest,
    LancarItemRequest,
)
from src.schemas.fechamento import AplicarDescontoRequest, FecharComandaRequest
from src.services import comandas_service

router = APIRouter()


@router.post("", response_model=ComandaResponse, status_code=201)
def abrir_comanda(
    body: ComandaCreateRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ComandaResponse:
    return comandas_service.abrir_comanda(db, body)  # type: ignore[return-value]


@router.get("", response_model=list[ComandaResponse])
def list_comandas(
    busca: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> list[ComandaResponse]:
    from src.repositories import comandas_repository
    from src.services.comandas_service import _build_response
    comandas = comandas_repository.list_abertas(db, busca)
    return [_build_response(db, c) for c in comandas]  # type: ignore[return-value]


@router.get("/{comanda_id}", response_model=ComandaResponse)
def get_comanda(
    comanda_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ComandaResponse:
    return comandas_service.get_comanda(db, comanda_id)  # type: ignore[return-value]


@router.post("/{comanda_id}/itens", response_model=ComandaResponse)
def lancar_item(
    comanda_id: int,
    body: LancarItemRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ComandaResponse:
    return comandas_service.lancar_item(db, comanda_id, body)  # type: ignore[return-value]


@router.patch("/{comanda_id}/itens/{item_id}", response_model=ComandaResponse)
def editar_item(
    comanda_id: int,
    item_id: int,
    body: EditarItemRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ComandaResponse:
    return comandas_service.editar_item(db, comanda_id, item_id, body)  # type: ignore[return-value]


@router.post("/{comanda_id}/itens/{item_id}/cancelar", response_model=ComandaResponse)
def cancelar_item(
    comanda_id: int,
    item_id: int,
    body: CancelarItemRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ComandaResponse:
    return comandas_service.cancelar_item(db, comanda_id, item_id, body)  # type: ignore[return-value]


@router.post("/{comanda_id}/desconto", response_model=ComandaResponse)
def aplicar_desconto(
    comanda_id: int,
    body: AplicarDescontoRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ComandaResponse:
    return comandas_service.aplicar_desconto(db, comanda_id, body)  # type: ignore[return-value]


@router.post("/{comanda_id}/fechar", response_model=ComandaResponse)
def fechar_comanda(
    comanda_id: int,
    body: FecharComandaRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ComandaResponse:
    return comandas_service.fechar_comanda(db, comanda_id, body)  # type: ignore[return-value]
