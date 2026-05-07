from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.schemas.compras import CompraCreateRequest, CompraResponse
from src.services import compras_service

router = APIRouter()


@router.post("", response_model=CompraResponse, status_code=status.HTTP_201_CREATED)
def create_compra(
    data: CompraCreateRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> CompraResponse:
    return compras_service.criar_compra(db, data)


@router.get("", response_model=list[CompraResponse])
def list_compras(
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    fornecedor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> list[CompraResponse]:
    return compras_service.list_compras(db, data_inicio, data_fim, fornecedor_id)  # type: ignore[return-value]


@router.get("/{compra_id}", response_model=CompraResponse)
def get_compra(
    compra_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> CompraResponse:
    return compras_service.get_compra(db, compra_id)
