import math
from typing import Optional

from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.garcons import Garcom
from src.repositories import garcons_repository
from src.schemas.garcons import (
    GarcomCreateRequest,
    GarcomPageResponse,
    GarcomResponse,
    GarcomUpdateRequest,
)


def list_garcons(
    db: Session,
    busca: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 500,
) -> GarcomPageResponse:
    items, total = garcons_repository.list_all(db, busca=busca, pagina=pagina, por_pagina=por_pagina)
    return GarcomPageResponse(
        itens=[GarcomResponse.model_validate(i) for i in items],
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=math.ceil(total / por_pagina) if total > 0 else 1,
    )


def get_garcom(db: Session, garcom_id: int) -> Garcom:
    obj = garcons_repository.get_by_id(db, garcom_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Garçom não encontrado", http_status=404)
    return obj


def create_garcom(db: Session, data: GarcomCreateRequest) -> Garcom:
    return garcons_repository.create(db, data)


def update_garcom(db: Session, garcom_id: int, data: GarcomUpdateRequest) -> Garcom:
    obj = garcons_repository.update(db, garcom_id, data)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Garçom não encontrado", http_status=404)
    return obj


def toggle_ativo_garcom(db: Session, garcom_id: int) -> Garcom:
    obj = garcons_repository.get_by_id(db, garcom_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Garçom não encontrado", http_status=404)
    obj.ativo = not obj.ativo
    db.commit()
    db.refresh(obj)
    return obj
