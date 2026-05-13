from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.schemas.produtos import ProdutoCreateRequest, ProdutoResponse, ProdutoUpdateRequest
from src.services import produtos_service

router = APIRouter()


@router.get("/top", response_model=list[ProdutoResponse])
def top_produtos(
    dias: int = Query(7, ge=1),
    limit: int = Query(6, ge=1, le=50),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> list[ProdutoResponse]:
    return produtos_service.get_top_produtos(db, dias, limit)  # type: ignore[return-value]


@router.get("", response_model=list[ProdutoResponse])
def list_produtos(
    categoria_id: Optional[int] = Query(None),
    busca: Optional[str] = Query(None),
    ativo: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> list[ProdutoResponse]:
    return produtos_service.list_produtos(db, categoria_id, busca, ativo)  # type: ignore[return-value]


@router.get("/{produto_id}", response_model=ProdutoResponse)
def get_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ProdutoResponse:
    return produtos_service.get_produto(db, produto_id)  # type: ignore[return-value]


@router.post("", response_model=ProdutoResponse, status_code=201)
def create_produto(
    body: ProdutoCreateRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ProdutoResponse:
    return produtos_service.create_produto(db, body)  # type: ignore[return-value]


@router.put("/{produto_id}", response_model=ProdutoResponse)
def update_produto(
    produto_id: int,
    body: ProdutoUpdateRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ProdutoResponse:
    return produtos_service.update_produto(db, produto_id, body)  # type: ignore[return-value]


@router.patch("/{produto_id}/desativar", response_model=ProdutoResponse)
def desativar_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ProdutoResponse:
    return produtos_service.desativar_produto(db, produto_id)  # type: ignore[return-value]


@router.patch("/{produto_id}/reativar", response_model=ProdutoResponse)
def reativar_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ProdutoResponse:
    return produtos_service.reativar_produto(db, produto_id)  # type: ignore[return-value]


@router.delete("/{produto_id}", status_code=204)
def delete_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> None:
    produtos_service.delete_produto(db, produto_id)
