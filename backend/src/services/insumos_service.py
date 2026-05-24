import math
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.insumos import Insumo
from src.repositories import insumos_repository
from src.schemas.insumos import (
    InsumoCreateRequest,
    InsumoPageResponse,
    InsumoResponse,
    InsumoUpdateRequest,
)


def list_insumos(
    db: Session,
    categoria_id: Optional[int] = None,
    busca: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 500,
) -> InsumoPageResponse:
    items, total = insumos_repository.list_ativos(db, categoria_id, busca, pagina=pagina, por_pagina=por_pagina)
    return InsumoPageResponse(
        itens=[InsumoResponse.model_validate(i) for i in items],
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=math.ceil(total / por_pagina) if total > 0 else 1,
    )


def list_all_insumos(
    db: Session,
    busca: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 500,
) -> InsumoPageResponse:
    items, total = insumos_repository.list_all(db, busca, pagina=pagina, por_pagina=por_pagina)
    return InsumoPageResponse(
        itens=[InsumoResponse.model_validate(i) for i in items],
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=math.ceil(total / por_pagina) if total > 0 else 1,
    )


def get_insumo(db: Session, insumo_id: int) -> InsumoResponse:
    obj = insumos_repository.get_by_id(db, insumo_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Insumo não encontrado", http_status=404)
    return InsumoResponse.model_validate(obj)


def create_insumo(db: Session, data: InsumoCreateRequest) -> InsumoResponse:
    try:
        obj = insumos_repository.create(db, data)
    except IntegrityError:
        db.rollback()
        existing = db.execute(select(Insumo).where(Insumo.nome == data.nome)).scalar_one_or_none()
        if existing and not existing.ativo:
            raise AppError(ErrorCode.CONFLICT, "Insumo inativo com este nome já existe. Reative-o em Cadastros → Insumos.", http_status=409) from None
        raise AppError(ErrorCode.CONFLICT, "Já existe um insumo com este nome", http_status=409) from None
    return InsumoResponse.model_validate(obj)


def update_insumo(db: Session, insumo_id: int, data: InsumoUpdateRequest) -> InsumoResponse:
    try:
        obj = insumos_repository.update(db, insumo_id, data)
    except IntegrityError:
        db.rollback()
        raise AppError(ErrorCode.CONFLICT, "Já existe um insumo com este nome", http_status=409) from None
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Insumo não encontrado", http_status=404)
    return InsumoResponse.model_validate(obj)


def toggle_insumo_ativo(db: Session, insumo_id: int) -> InsumoResponse:
    obj = insumos_repository.toggle_ativo(db, insumo_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Insumo não encontrado", http_status=404)
    return InsumoResponse.model_validate(obj)


def delete_insumo(db: Session, insumo_id: int) -> None:
    obj = insumos_repository.get_by_id(db, insumo_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Insumo não encontrado", http_status=404)
    if insumos_repository.is_referenced_in_ficha(db, insumo_id):
        insumos_repository.soft_delete(db, insumo_id)
    else:
        insumos_repository.hard_delete(db, insumo_id)
