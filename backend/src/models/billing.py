from __future__ import annotations

import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Plano(Base):
    __tablename__ = "planos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    descricao: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    preco_mensal: Mapped[Decimal] = mapped_column(sa.Numeric(10, 2), nullable=False)
    ativo: Mapped[bool] = mapped_column(sa.Boolean(), nullable=False, server_default=sa.text("true"), default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        server_default=sa.text("NOW()"),
    )


class PagamentoAssinatura(Base):
    __tablename__ = "pagamentos_assinatura"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        sa.BigInteger(),
        sa.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    valor: Mapped[Decimal] = mapped_column(sa.Numeric(10, 2), nullable=False)
    data_pagamento: Mapped[datetime.date] = mapped_column(sa.Date(), nullable=False)
    data_vencimento: Mapped[datetime.date | None] = mapped_column(sa.Date(), nullable=True)
    gateway_ref: Mapped[str | None] = mapped_column(sa.String(200), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        server_default=sa.text("NOW()"),
    )
