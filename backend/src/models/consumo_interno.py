import datetime
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ItemConsumoInterno(Base):
    __tablename__ = "itens_consumo_interno"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False, server_default=sa.text("(NULLIF(current_setting('app.tenant_id', true), ''))::bigint"))
    consumidor_id: Mapped[int] = mapped_column(sa.ForeignKey("system_users.id"), nullable=False)
    produto_id: Mapped[int] = mapped_column(sa.ForeignKey("produtos.id"), nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(sa.Numeric(10, 4), nullable=False)
    custo_unitario: Mapped[Decimal] = mapped_column(sa.Numeric(10, 4), nullable=False)
    observacao: Mapped[Optional[str]] = mapped_column(sa.Text(), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(), nullable=False, server_default=sa.func.now()
    )
