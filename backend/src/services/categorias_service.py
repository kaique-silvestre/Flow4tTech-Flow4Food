
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.categorias import Categoria
from src.repositories import categorias_repository
from src.schemas.categorias import CategoriaCreateRequest, CategoriaUpdateRequest


def list_categorias(db: Session) -> list[Categoria]:
    return categorias_repository.list_all(db)


def get_categoria(db: Session, categoria_id: int) -> Categoria:
    obj = categorias_repository.get_by_id(db, categoria_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Categoria não encontrada", http_status=404)
    return obj


def create_categoria(db: Session, data: CategoriaCreateRequest) -> Categoria:
    return categorias_repository.create(db, data.nome)


def update_categoria(db: Session, categoria_id: int, data: CategoriaUpdateRequest) -> Categoria:
    obj = categorias_repository.update(db, categoria_id, data.nome)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Categoria não encontrada", http_status=404)
    return obj


def delete_categoria(db: Session, categoria_id: int) -> None:
    deleted = categorias_repository.delete(db, categoria_id)
    if not deleted:
        raise AppError(ErrorCode.NOT_FOUND, "Categoria não encontrada", http_status=404)
