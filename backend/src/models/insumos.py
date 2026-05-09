import enum
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class UnidadeBase(str, enum.Enum):
    UNIDADE = "un"
    GRAMA = "g"
    QUILOGRAMA = "kg"
    MILILITRO = "ml"
    LITRO = "l"


class Insumo(Base):
    __tablename__ = "insumos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    categoria_id: Mapped[Optional[int]] = mapped_column(sa.ForeignKey("categorias.id"), nullable=True)
    unidade_base: Mapped[str] = mapped_column(sa.Enum(UnidadeBase, native_enum=False), nullable=False)
    quantidade_caixa: Mapped[Optional[int]] = mapped_column(nullable=True)
    custo_medio: Mapped[Optional[Decimal]] = mapped_column(sa.Numeric(10, 4), nullable=True)
    estoque_atual: Mapped[Decimal] = mapped_column(sa.Numeric(12, 4), nullable=False, default=Decimal("0"))
    ativo: Mapped[bool] = mapped_column(nullable=False, default=True)
