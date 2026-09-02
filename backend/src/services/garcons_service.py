import math
from decimal import Decimal
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.comissoes_garcom import ComissaoGarcom
from src.models.garcons import Garcom
from src.repositories import garcons_repository
from src.schemas.garcons import (
    GarcomCreateRequest,
    GarcomPageResponse,
    GarcomResponse,
    GarcomUpdateRequest,
)


def _is_nome_unique_violation(error: IntegrityError) -> bool:
    """Detecta se o IntegrityError foi causado pela unique constraint uq_garcons_tenant_nome.

    Postgres (psycopg2): usa o pgcode '23505' (unique_violation).
    SQLite (testes): cai para inspeção textual ("UNIQUE constraint failed").
    """
    pgcode = getattr(error.orig, "pgcode", None)
    if pgcode is not None:
        return pgcode == "23505"
    msg = str(error.orig).lower()
    return "unique" in msg


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
    try:
        return garcons_repository.create(db, data)
    except IntegrityError as e:
        db.rollback()
        if _is_nome_unique_violation(e):
            raise AppError(ErrorCode.CONFLICT, "Já existe um garçom com este nome", http_status=409) from None
        raise


def update_garcom(db: Session, garcom_id: int, data: GarcomUpdateRequest) -> Garcom:
    try:
        obj = garcons_repository.update(db, garcom_id, data)
    except IntegrityError as e:
        db.rollback()
        if _is_nome_unique_violation(e):
            raise AppError(ErrorCode.CONFLICT, "Já existe um garçom com este nome", http_status=409) from None
        raise
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


def update_comissao(db: Session, comissao_id: int, valor: Decimal) -> ComissaoGarcom:
    comissao = db.get(ComissaoGarcom, comissao_id)
    if comissao is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comissão não encontrada", http_status=404)
    if comissao.pago:
        raise AppError(
            ErrorCode.CONFLICT,
            "Comissão já paga não pode ser alterada",
            http_status=409,
        )
    comissao.valor = valor
    db.commit()
    db.refresh(comissao)
    return comissao


def toggle_pago_comissao(db: Session, comissao_id: int) -> ComissaoGarcom:
    comissao = db.get(ComissaoGarcom, comissao_id)
    if comissao is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comissão não encontrada", http_status=404)
    comissao.pago = not comissao.pago
    db.commit()
    db.refresh(comissao)
    return comissao


def delete_comissao(db: Session, comissao_id: int) -> None:
    comissao = db.get(ComissaoGarcom, comissao_id)
    if comissao is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comissão não encontrada", http_status=404)
    db.delete(comissao)
    db.commit()
