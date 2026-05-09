
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.schemas.metodos_pagamento import (
    MetodoPagamentoCreateRequest,
    MetodoPagamentoResponse,
    MetodoPagamentoUpdateRequest,
)
from src.services import metodos_pagamento_service

router = APIRouter()


@router.get("", response_model=list[MetodoPagamentoResponse])
def list_metodos(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> list[MetodoPagamentoResponse]:
    return metodos_pagamento_service.list_metodos(db)  # type: ignore[return-value]


@router.post("", response_model=MetodoPagamentoResponse, status_code=201)
def create_metodo(
    body: MetodoPagamentoCreateRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> MetodoPagamentoResponse:
    return metodos_pagamento_service.create_metodo(db, body)  # type: ignore[return-value]


@router.put("/{metodo_id}", response_model=MetodoPagamentoResponse)
def update_metodo(
    metodo_id: int,
    body: MetodoPagamentoUpdateRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> MetodoPagamentoResponse:
    return metodos_pagamento_service.update_metodo(db, metodo_id, body)  # type: ignore[return-value]


@router.delete("/{metodo_id}", status_code=204)
def delete_metodo(
    metodo_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> None:
    metodos_pagamento_service.delete_metodo(db, metodo_id)
