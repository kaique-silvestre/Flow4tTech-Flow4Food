import math
from typing import Optional

from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.fornecedores import Fornecedor
from src.repositories import fornecedores_repository
from src.schemas.fornecedores import (
    FornecedorCreateRequest,
    FornecedorPageResponse,
    FornecedorResponse,
    FornecedorUpdateRequest,
)


def list_fornecedores(
    db: Session,
    busca: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 500,
) -> FornecedorPageResponse:
    items, total = fornecedores_repository.list_all(db, busca=busca, pagina=pagina, por_pagina=por_pagina)
    return FornecedorPageResponse(
        itens=[FornecedorResponse.model_validate(i) for i in items],
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=math.ceil(total / por_pagina) if total > 0 else 1,
    )


def get_fornecedor(db: Session, fornecedor_id: int) -> Fornecedor:
    obj = fornecedores_repository.get_by_id(db, fornecedor_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Fornecedor não encontrado", http_status=404)
    return obj


def create_fornecedor(db: Session, data: FornecedorCreateRequest) -> Fornecedor:
    return fornecedores_repository.create(db, data)


def update_fornecedor(db: Session, fornecedor_id: int, data: FornecedorUpdateRequest) -> Fornecedor:
    obj = fornecedores_repository.update(db, fornecedor_id, data)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Fornecedor não encontrado", http_status=404)
    return obj


def toggle_ativo_fornecedor(db: Session, fornecedor_id: int) -> Fornecedor:
    obj = fornecedores_repository.toggle_ativo(db, fornecedor_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Fornecedor não encontrado", http_status=404)
    return obj


def delete_fornecedor(db: Session, fornecedor_id: int) -> None:
    deleted = fornecedores_repository.delete(db, fornecedor_id)
    if not deleted:
        raise AppError(ErrorCode.NOT_FOUND, "Fornecedor não encontrado", http_status=404)
