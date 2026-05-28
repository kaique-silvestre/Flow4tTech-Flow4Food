import datetime
import enum
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class MotivoCancelamento(str, enum.Enum):
    CLIENTE_DESISTIU = "cliente_desistiu"
    ERRO_LANCAMENTO = "erro_lancamento"
    ITEM_INDISPONIVEL = "item_indisponivel"
    OUTRO = "outro"


class ItemComanda(Base):
    __tablename__ = "itens_comanda"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False, server_default="1")
    comanda_id: Mapped[int] = mapped_column(nullable=False)
    produto_id: Mapped[int] = mapped_column(nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(nullable=False)
    preco_unitario: Mapped[Decimal] = mapped_column(nullable=False)
    pessoa_associada: Mapped[Optional[str]] = mapped_column(nullable=True)
    observacao: Mapped[Optional[str]] = mapped_column(nullable=True)
    cortesia: Mapped[bool] = mapped_column(nullable=False, default=False)
    cancelado: Mapped[bool] = mapped_column(nullable=False, default=False)
    motivo_cancelamento: Mapped[Optional[str]] = mapped_column(nullable=True)
    estornado: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(nullable=False, server_default=func.now())
