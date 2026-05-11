
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.metodos_pagamento import MetodoPagamento
from src.models.pagamentos import Pagamento
from src.repositories import metodos_pagamento_repository
from src.schemas.metodos_pagamento import MetodoPagamentoCreateRequest, MetodoPagamentoUpdateRequest


def list_metodos(db: Session) -> list[MetodoPagamento]:
    return metodos_pagamento_repository.list_all(db)


def get_metodo(db: Session, metodo_id: int) -> MetodoPagamento:
    obj = metodos_pagamento_repository.get_by_id(db, metodo_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Método de pagamento não encontrado", http_status=404)
    return obj


def create_metodo(db: Session, data: MetodoPagamentoCreateRequest) -> MetodoPagamento:
    return metodos_pagamento_repository.create(db, data)


def update_metodo(db: Session, metodo_id: int, data: MetodoPagamentoUpdateRequest) -> MetodoPagamento:
    obj = metodos_pagamento_repository.update(db, metodo_id, data)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Método de pagamento não encontrado", http_status=404)
    return obj


def toggle_ativo_metodo(db: Session, metodo_id: int) -> MetodoPagamento:
    obj = metodos_pagamento_repository.get_by_id(db, metodo_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Método de pagamento não encontrado", http_status=404)
    obj.ativo = not obj.ativo
    db.commit()
    db.refresh(obj)
    return obj


def delete_metodo(db: Session, metodo_id: int) -> None:
    get_metodo(db, metodo_id)
    count = db.execute(
        select(func.count()).where(Pagamento.metodo_id == metodo_id)
    ).scalar()
    if count and count > 0:
        raise AppError(ErrorCode.CONFLICT, "Método possui histórico de pagamentos", http_status=409)
    metodos_pagamento_repository.delete(db, metodo_id)
