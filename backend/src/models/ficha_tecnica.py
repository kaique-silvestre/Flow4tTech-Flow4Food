from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class FichaTecnica(Base):
    __tablename__ = "ficha_tecnica"

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(sa.ForeignKey("produtos.id"), nullable=False)
    insumo_id: Mapped[int] = mapped_column(sa.ForeignKey("insumos.id"), nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(sa.Numeric(10, 4), nullable=False)
