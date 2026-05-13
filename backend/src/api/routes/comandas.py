from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.repositories import comandas_repository as _cr
from src.schemas.comandas import (
    CancelarItemRequest,
    ComandaCreateRequest,
    ComandaResponse,
    EditarItemRequest,
    LancarItemRequest,
    PatchComandaRequest,
)
from src.schemas.comprovante import ComprovanteResponse
from src.schemas.fechamento import AplicarDescontoRequest, FecharComandaRequest
from src.services import comandas_service, comprovante_service
from src.services.comandas_service import _build_response

router = APIRouter()


@router.post("", response_model=ComandaResponse, status_code=201)
def abrir_comanda(
    body: ComandaCreateRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ComandaResponse:
    return comandas_service.abrir_comanda(db, body)  # type: ignore[return-value]


@router.get("/fechadas", response_model=list[ComandaResponse])
def list_fechadas(
    busca: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),
    data_fim: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> list[ComandaResponse]:
    import datetime as dt
    dt_inicio = dt.datetime.strptime(data_inicio, "%Y-%m-%d") if data_inicio else None
    dt_fim = (
        dt.datetime.strptime(data_fim, "%Y-%m-%d") + dt.timedelta(days=1) - dt.timedelta(seconds=1)
        if data_fim
        else None
    )
    comandas = _cr.list_fechadas(db, busca, dt_inicio, dt_fim)
    return [_build_response(db, c) for c in comandas]  # type: ignore[return-value]


@router.get("/count-abertas", response_model=int)
def count_abertas(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> int:
    from src.repositories import comandas_repository
    return comandas_repository.count_abertas(db)


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


@router.patch("/{comanda_id}", response_model=ComandaResponse)
def patch_comanda(
    comanda_id: int,
    body: PatchComandaRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ComandaResponse:
    return comandas_service.patch_comanda(db, comanda_id, body)  # type: ignore[return-value]


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


@router.post("/{comanda_id}/reabrir", response_model=ComandaResponse)
def reabrir_comanda(
    comanda_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ComandaResponse:
    return comandas_service.reabrir_comanda(db, comanda_id)  # type: ignore[return-value]


@router.post("/{comanda_id}/cancelar", response_model=ComandaResponse)
def cancelar_comanda(
    comanda_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ComandaResponse:
    return comandas_service.cancelar_comanda(db, comanda_id)  # type: ignore[return-value]


@router.get("/{comanda_id}/comprovante", response_model=ComprovanteResponse)
def get_comprovante(
    comanda_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ComprovanteResponse:
    return comprovante_service.build_comprovante(db, comanda_id)  # type: ignore[return-value]
