import datetime
import enum
from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class StatusComanda(str, enum.Enum):
    ABERTA = "aberta"
    FECHADA = "fechada"
    CANCELADA = "cancelada"


class Comanda(Base):
    __tablename__ = "comandas"

    id: Mapped[int] = mapped_column(primary_key=True)
    identificacao: Mapped[str] = mapped_column(nullable=False)
    tipo_identificacao: Mapped[str] = mapped_column(nullable=False)
    garcom_id: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default=StatusComanda.ABERTA.value)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    pessoas: Mapped[Optional[str]] = mapped_column(nullable=True)
    desconto_percentual: Mapped[Optional[Decimal]] = mapped_column(nullable=True)
    desconto_valor: Mapped[Optional[Decimal]] = mapped_column(nullable=True)
    total: Mapped[Optional[Decimal]] = mapped_column(nullable=True)
    saldo_pendente: Mapped[Optional[Decimal]] = mapped_column(nullable=True)
    data_fechamento: Mapped[Optional[datetime.datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())
