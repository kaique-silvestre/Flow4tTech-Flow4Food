from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.metodos_pagamento import MetodoPagamento
from src.schemas.metodos_pagamento import MetodoPagamentoCreateRequest, MetodoPagamentoUpdateRequest


def list_all(db: Session) -> list[MetodoPagamento]:
    return list(db.execute(select(MetodoPagamento).order_by(MetodoPagamento.nome)).scalars().all())


def get_by_id(db: Session, metodo_id: int) -> Optional[MetodoPagamento]:
    return db.execute(select(MetodoPagamento).where(MetodoPagamento.id == metodo_id)).scalar_one_or_none()


def create(db: Session, data: MetodoPagamentoCreateRequest) -> MetodoPagamento:
    obj = MetodoPagamento(nome=data.nome, ativo=True)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, metodo_id: int, data: MetodoPagamentoUpdateRequest) -> Optional[MetodoPagamento]:
    obj = get_by_id(db, metodo_id)
    if obj is None:
        return None
    obj.nome = data.nome
    obj.ativo = data.ativo
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, metodo_id: int) -> None:
    obj = get_by_id(db, metodo_id)
    if obj is None:
        return
    db.delete(obj)
    db.commit()
