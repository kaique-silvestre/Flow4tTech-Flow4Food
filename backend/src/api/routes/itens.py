from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.schemas.itens import ItemCreateRequest, ItemResponse, ItemUpdateRequest
from src.services import comandas_service, itens_service

router = APIRouter()


@router.get("/top", response_model=list[ItemResponse])
def top_itens(
    dias: int = Query(7, ge=1),
    limit: int = Query(6, ge=1, le=50),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> list[ItemResponse]:
    return comandas_service.get_top_itens(db, dias, limit)  # type: ignore[return-value]


@router.get("", response_model=list[ItemResponse])
def list_itens(
    categoria_id: Optional[int] = Query(None),
    tipo: Optional[str] = Query(None),
    vendavel: Optional[bool] = Query(None),
    busca: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> list[ItemResponse]:
    return itens_service.list_itens(db, categoria_id, tipo, vendavel, busca)  # type: ignore[return-value]


@router.get("/simples", response_model=list[ItemResponse])
def list_simples(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> list[ItemResponse]:
    return itens_service.list_simples_ativos(db)  # type: ignore[return-value]


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ItemResponse:
    return itens_service.get_item(db, item_id)  # type: ignore[return-value]


@router.post("", response_model=ItemResponse, status_code=201)
def create_item(
    body: ItemCreateRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ItemResponse:
    return itens_service.create_item(db, body)  # type: ignore[return-value]


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    body: ItemUpdateRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ItemResponse:
    return itens_service.update_item(db, item_id, body)  # type: ignore[return-value]


@router.delete("/{item_id}", status_code=204)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> None:
    itens_service.delete_item(db, item_id)
