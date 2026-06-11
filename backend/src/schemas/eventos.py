import datetime
from typing import Optional

from pydantic import BaseModel


class EventoCreate(BaseModel):
    titulo: str
    descricao: Optional[str] = None  # noqa: UP045
    data_evento: datetime.date


class EventoPatch(BaseModel):
    titulo: Optional[str] = None  # noqa: UP045
    descricao: Optional[str] = None  # noqa: UP045


class EventoResponse(BaseModel):
    id: int
    tenant_id: int
    titulo: str
    descricao: Optional[str] = None  # noqa: UP045
    data_evento: datetime.date
    criado_por: Optional[int] = None  # noqa: UP045
    created_at: Optional[datetime.datetime] = None  # noqa: UP045

    model_config = {"from_attributes": True}
