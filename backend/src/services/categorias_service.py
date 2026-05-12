from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.repositories import categorias_repository
from src.schemas.categorias import (
    CategoriaCreateRequest,
    CategoriaResponse,
    CategoriaUpdateRequest,
)


def _build_tree(db: Session) -> list[CategoriaResponse]:
    all_cats = categorias_repository.list_all(db)
    children_map: dict[int, list] = {}
    for c in all_cats:
        if c.parent_id is not None:
            children_map.setdefault(c.parent_id, []).append(c)

    result = []
    for c in sorted([c for c in all_cats if c.parent_id is None], key=lambda x: x.nome):
        kids = sorted(children_map.get(c.id, []), key=lambda x: x.nome)
        result.append(
            CategoriaResponse(
                id=c.id,
                nome=c.nome,
                parent_id=c.parent_id,
                ativo=c.ativo,
                children=[
                    CategoriaResponse(id=k.id, nome=k.nome, parent_id=k.parent_id, ativo=k.ativo, children=[])
                    for k in kids
                ],
            )
        )
    return result


def list_categorias(db: Session) -> list[CategoriaResponse]:
    return _build_tree(db)


def toggle_ativo_categoria(db: Session, categoria_id: int) -> CategoriaResponse:
    obj = categorias_repository.toggle_ativo(db, categoria_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Categoria não encontrada", http_status=404)
    return CategoriaResponse(id=obj.id, nome=obj.nome, parent_id=obj.parent_id, ativo=obj.ativo, children=[])


def get_categoria(db: Session, categoria_id: int) -> CategoriaResponse:
    obj = categorias_repository.get_by_id(db, categoria_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Categoria não encontrada", http_status=404)
    return CategoriaResponse(id=obj.id, nome=obj.nome, parent_id=obj.parent_id, ativo=obj.ativo, children=[])


def create_categoria(db: Session, data: CategoriaCreateRequest) -> CategoriaResponse:
    if data.parent_id is not None:
        parent = categorias_repository.get_by_id(db, data.parent_id)
        if parent is None:
            raise AppError(ErrorCode.NOT_FOUND, "Categoria pai não encontrada", http_status=404)
        if parent.parent_id is not None:
            raise AppError(
                ErrorCode.NIVEL_MAX_ATINGIDO,
                "Máximo de 2 níveis permitidos (pai + filho)",
                http_status=422,
            )
    obj = categorias_repository.create(db, data.nome, data.parent_id)
    return CategoriaResponse(id=obj.id, nome=obj.nome, parent_id=obj.parent_id, ativo=obj.ativo, children=[])


def update_categoria(
    db: Session, categoria_id: int, data: CategoriaUpdateRequest
) -> CategoriaResponse:
    if data.parent_id is not None:
        parent = categorias_repository.get_by_id(db, data.parent_id)
        if parent is None:
            raise AppError(ErrorCode.NOT_FOUND, "Categoria pai não encontrada", http_status=404)
        if parent.parent_id is not None:
            raise AppError(
                ErrorCode.NIVEL_MAX_ATINGIDO,
                "Máximo de 2 níveis permitidos (pai + filho)",
                http_status=422,
            )
        if data.parent_id == categoria_id:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Categoria não pode ser pai de si mesma",
                http_status=422,
            )
    obj = categorias_repository.update(db, categoria_id, data.nome, data.parent_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Categoria não encontrada", http_status=404)
    return CategoriaResponse(id=obj.id, nome=obj.nome, parent_id=obj.parent_id, ativo=obj.ativo, children=[])


def delete_categoria(db: Session, categoria_id: int) -> None:
    obj = categorias_repository.get_by_id(db, categoria_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Categoria não encontrada", http_status=404)
    if categorias_repository.has_children(db, categoria_id):
        raise AppError(
            ErrorCode.HAS_CHILDREN,
            "Categoria possui subcategorias ativas. Remova-as primeiro.",
            http_status=409,
        )
    categorias_repository.delete(db, categoria_id)
