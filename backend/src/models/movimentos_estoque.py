import datetime
import enum
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class TipoMovimento(str, enum.Enum):
    ENTRADA = "entrada"
    SAIDA_VENDA = "saida_venda"
    SAIDA_PERDA = "saida_perda"
    ENTRADA_ESTORNO = "entrada_estorno"


class MotivoPerda(str, enum.Enum):
    CONSUMO_INTERNO = "consumo_interno"
    PERDA = "perda"
    QUEBRA = "quebra"
    CORTESIA = "cortesia"
    OUTRO = "outro"


class MovimentoEstoque(Base):
    __tablename__ = "movimentos_estoque"

    id: Mapped[int] = mapped_column(primary_key=True)
    insumo_id: Mapped[int] = mapped_column(sa.ForeignKey("insumos.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(
        sa.Enum(TipoMovimento, native_enum=False), nullable=False
    )
    quantidade: Mapped[Decimal] = mapped_column(sa.Numeric(12, 4), nullable=False)
    custo_unitario: Mapped[Optional[Decimal]] = mapped_column(sa.Numeric(10, 4), nullable=True)
    saldo_apos: Mapped[Decimal] = mapped_column(sa.Numeric(12, 4), nullable=False)
    motivo: Mapped[Optional[str]] = mapped_column(sa.String(30), nullable=True)
    observacao: Mapped[Optional[str]] = mapped_column(sa.String(500), nullable=True)
    compra_id: Mapped[Optional[int]] = mapped_column(sa.ForeignKey("compras.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(), nullable=False, server_default=sa.func.now()
    )
