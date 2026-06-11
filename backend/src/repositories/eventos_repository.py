import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.models.eventos import TenantEvento
from src.schemas.eventos import EventoCreate, EventoPatch


def list_by_month(db: Session, year: int, month: int) -> list[TenantEvento]:
    start = datetime.date(year, month, 1)
    end = datetime.date(year + 1, 1, 1) if month == 12 else datetime.date(year, month + 1, 1)
    return (
        db.query(TenantEvento)
        .filter(TenantEvento.data_evento >= start, TenantEvento.data_evento < end)
        .order_by(TenantEvento.data_evento)
        .all()
    )


def get_by_id(db: Session, evento_id: int) -> Optional[TenantEvento]:  # noqa: UP045
    return db.query(TenantEvento).filter(TenantEvento.id == evento_id).first()


def create(db: Session, data: EventoCreate, criado_por: Optional[int] = None) -> TenantEvento:  # noqa: UP045
    evento = TenantEvento(
        titulo=data.titulo,
        descricao=data.descricao,
        data_evento=data.data_evento,
        criado_por=criado_por,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        updated_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return evento


def update(db: Session, evento: TenantEvento, data: EventoPatch) -> TenantEvento:
    if data.titulo is not None:
        evento.titulo = data.titulo
    if data.descricao is not None:
        evento.descricao = data.descricao
    evento.updated_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    db.refresh(evento)
    return evento


def delete(db: Session, evento: TenantEvento) -> None:
    db.delete(evento)
    db.commit()
