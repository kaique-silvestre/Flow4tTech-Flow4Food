import datetime
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Pagamento(Base):
    __tablename__ = "pagamentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    comanda_id: Mapped[int] = mapped_column(sa.ForeignKey("comandas.id"), nullable=False)
    metodo_id: Mapped[int] = mapped_column(sa.ForeignKey("metodos_pagamento.id"), nullable=False)
    valor: Mapped[Decimal] = mapped_column(sa.Numeric(10, 2), nullable=False)
    valor_nota: Mapped[Optional[Decimal]] = mapped_column(sa.Numeric(10, 2), nullable=True)
    troco: Mapped[Optional[Decimal]] = mapped_column(sa.Numeric(10, 2), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(nullable=False, server_default=sa.func.now())
