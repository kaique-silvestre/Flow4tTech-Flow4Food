import datetime
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Compra(Base):
    __tablename__ = "compras"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False, server_default="1")
    fornecedor_id: Mapped[Optional[int]] = mapped_column(sa.ForeignKey("fornecedores.id"), nullable=True)
    data_compra: Mapped[datetime.date] = mapped_column(sa.Date(), nullable=False)
    numero_nota: Mapped[Optional[str]] = mapped_column(sa.String(50), nullable=True)
    total: Mapped[Decimal] = mapped_column(sa.Numeric(12, 2), nullable=False, default=Decimal("0"))
    # status: rascunho | confirmado | recebido | pago | cancelado
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, server_default="recebido")
    # tipo_compra: imediata | agendada | a_prazo
    tipo_compra: Mapped[str] = mapped_column(sa.String(20), nullable=False, server_default="imediata")
    data_prevista_recebimento: Mapped[Optional[datetime.date]] = mapped_column(sa.Date(), nullable=True)
    data_real_recebimento: Mapped[Optional[datetime.date]] = mapped_column(sa.Date(), nullable=True)
    data_prevista_pagamento: Mapped[Optional[datetime.date]] = mapped_column(sa.Date(), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(), nullable=False, server_default=sa.func.now()
    )


class ItemCompra(Base):
    __tablename__ = "itens_compra"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False, server_default="1")
    compra_id: Mapped[int] = mapped_column(sa.ForeignKey("compras.id"), nullable=False)
    insumo_id: Mapped[int] = mapped_column(sa.ForeignKey("insumos.id"), nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(sa.Numeric(12, 4), nullable=False)
    custo_unitario: Mapped[Decimal] = mapped_column(sa.Numeric(10, 4), nullable=False)
    custo_total: Mapped[Decimal] = mapped_column(sa.Numeric(12, 2), nullable=False)
