import datetime
import enum
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class TipoEvento(str, enum.Enum):
    COMANDA_ABERTA = "comanda_aberta"
    COMANDA_EDITADA = "comanda_editada"
    ITEM_LANCADO = "item_lancado"
    ITEM_EDITADO = "item_editado"
    ITEM_CANCELADO = "item_cancelado"
    COMANDA_REABERTA = "comanda_reaberta"


class EventoComanda(Base):
    __tablename__ = "eventos_comanda"

    id: Mapped[int] = mapped_column(primary_key=True)
    comanda_id: Mapped[int] = mapped_column(nullable=False)
    tipo: Mapped[str] = mapped_column(nullable=False)
    payload: Mapped[Optional[str]] = mapped_column(nullable=True)
    garcom_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(nullable=False, server_default=func.now())
