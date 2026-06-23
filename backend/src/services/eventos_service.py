import datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.repositories import eventos_repository
from src.schemas.eventos import EventoCreate, EventoPatch, EventoResponse


def list_by_month(db: Session, mes: Optional[str]) -> list[EventoResponse]:  # noqa: UP045
    if mes:
        try:
            dt = datetime.datetime.strptime(mes, "%Y-%m")
        except ValueError as exc:
            raise AppError(code=ErrorCode.VALIDATION_ERROR, message="Formato de mês inválido. Use YYYY-MM.", http_status=400) from exc
        year, month = dt.year, dt.month
    else:
        now = datetime.datetime.now()
        year, month = now.year, now.month
    eventos = eventos_repository.list_by_month(db, year, month)
    return [EventoResponse.model_validate(e) for e in eventos]


def criar_evento(db: Session, data: EventoCreate, criado_por: Optional[int] = None) -> EventoResponse:  # noqa: UP045
    evento = eventos_repository.create(db, data, criado_por)
    return EventoResponse.model_validate(evento)


def patch_evento(db: Session, evento_id: int, data: EventoPatch) -> EventoResponse:
    evento = eventos_repository.get_by_id(db, evento_id)
    if evento is None:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Evento não encontrado", http_status=404)
    evento = eventos_repository.update(db, evento, data)
    return EventoResponse.model_validate(evento)


def delete_evento(db: Session, evento_id: int) -> None:
    evento = eventos_repository.get_by_id(db, evento_id)
    if evento is None:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Evento não encontrado", http_status=404)
    eventos_repository.delete(db, evento)
