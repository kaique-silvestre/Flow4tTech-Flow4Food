from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ComponenteFicha(Base):
    __tablename__ = "componentes_ficha"

    id: Mapped[int] = mapped_column(primary_key=True)
    ficha_tecnica_id: Mapped[int] = mapped_column(sa.ForeignKey("fichas_tecnicas.id"), nullable=False)
    insumo_id: Mapped[int] = mapped_column(sa.ForeignKey("itens.id"), nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(sa.Numeric(10, 4), nullable=False)
