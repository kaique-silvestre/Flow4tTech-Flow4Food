from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    categoria_id: Mapped[Optional[int]] = mapped_column(sa.ForeignKey("categorias.id"), nullable=True)
    preco_venda: Mapped[Optional[Decimal]] = mapped_column(sa.Numeric(10, 2), nullable=True)
    ativo: Mapped[bool] = mapped_column(nullable=False, default=True)
