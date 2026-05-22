
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db, require_permission
from src.schemas.fornecedores import (
    FornecedorCreateRequest,
    FornecedorResponse,
    FornecedorUpdateRequest,
)
from src.services import fornecedores_service

router = APIRouter(dependencies=[Depends(require_permission("compras"))])


@router.get("", response_model=list[FornecedorResponse])
def list_fornecedores(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> list[FornecedorResponse]:
    return fornecedores_service.list_fornecedores(db)  # type: ignore[return-value]


@router.post("", response_model=FornecedorResponse, status_code=201)
def create_fornecedor(
    body: FornecedorCreateRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> FornecedorResponse:
    return fornecedores_service.create_fornecedor(db, body)  # type: ignore[return-value]


@router.put("/{fornecedor_id}", response_model=FornecedorResponse)
def update_fornecedor(
    fornecedor_id: int,
    body: FornecedorUpdateRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> FornecedorResponse:
    return fornecedores_service.update_fornecedor(db, fornecedor_id, body)  # type: ignore[return-value]


@router.patch("/{fornecedor_id}/toggle-ativo", response_model=FornecedorResponse)
def toggle_ativo_fornecedor(
    fornecedor_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> FornecedorResponse:
    return fornecedores_service.toggle_ativo_fornecedor(db, fornecedor_id)  # type: ignore[return-value]


@router.delete("/{fornecedor_id}", status_code=204)
def delete_fornecedor(
    fornecedor_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> None:
    fornecedores_service.delete_fornecedor(db, fornecedor_id)
