import datetime
import enum
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class StatusCaixa(str, enum.Enum):
    ABERTA = "aberta"
    FECHADA = "fechada"


class TipoMovimentoCaixa(str, enum.Enum):
    SANGRIA = "sangria"
    SUPRIMENTO = "suprimento"


class CaixaSessao(Base):
    __tablename__ = "caixa_sessoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False, server_default="1")
    status: Mapped[str] = mapped_column(nullable=False, default=StatusCaixa.ABERTA.value)
    valor_abertura: Mapped[Decimal] = mapped_column(sa.Numeric(10, 2), nullable=False)
    valor_informado: Mapped[Optional[Decimal]] = mapped_column(sa.Numeric(10, 2), nullable=True)
    valor_esperado: Mapped[Optional[Decimal]] = mapped_column(sa.Numeric(10, 2), nullable=True)
    diferenca: Mapped[Optional[Decimal]] = mapped_column(sa.Numeric(10, 2), nullable=True)
    aberto_por_user_id: Mapped[int] = mapped_column(nullable=False)
    fechado_por_user_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    opened_at: Mapped[datetime.datetime] = mapped_column(nullable=False, server_default=func.now())
    closed_at: Mapped[Optional[datetime.datetime]] = mapped_column(nullable=True)
    observacao: Mapped[Optional[str]] = mapped_column(nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(nullable=False, server_default=func.now())


class CaixaMovimento(Base):
    __tablename__ = "caixa_movimentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False, server_default="1")
    sessao_id: Mapped[int] = mapped_column(sa.ForeignKey("caixa_sessoes.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(nullable=False)
    valor: Mapped[Decimal] = mapped_column(sa.Numeric(10, 2), nullable=False)
    motivo: Mapped[str] = mapped_column(nullable=False)
    user_id: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(nullable=False, server_default=func.now())
