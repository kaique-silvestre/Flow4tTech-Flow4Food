from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.schemas.categorias import CategoriaCreateRequest, CategoriaResponse, CategoriaUpdateRequest
from src.services import categorias_service

router = APIRouter()


@router.get("", response_model=list[CategoriaResponse])
def list_categorias(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> list[CategoriaResponse]:
    return categorias_service.list_categorias(db)


@router.post("", response_model=CategoriaResponse, status_code=201)
def create_categoria(
    body: CategoriaCreateRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> CategoriaResponse:
    return categorias_service.create_categoria(db, body)


@router.put("/{categoria_id}", response_model=CategoriaResponse)
def update_categoria(
    categoria_id: int,
    body: CategoriaUpdateRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> CategoriaResponse:
    return categorias_service.update_categoria(db, categoria_id, body)


@router.patch("/{categoria_id}/toggle-ativo", response_model=CategoriaResponse)
def toggle_ativo_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> CategoriaResponse:
    return categorias_service.toggle_ativo_categoria(db, categoria_id)


@router.delete("/{categoria_id}", status_code=204)
def delete_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> None:
    categorias_service.delete_categoria(db, categoria_id)
