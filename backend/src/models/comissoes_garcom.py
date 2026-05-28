from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ComissaoGarcom(Base):
    __tablename__ = "comissoes_garcom"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False, server_default="1")
    garcom_id: Mapped[int] = mapped_column(sa.ForeignKey("garcons.id"), nullable=False)
    comanda_id: Mapped[int] = mapped_column(sa.ForeignKey("comandas.id"), nullable=False)
    valor: Mapped[Decimal] = mapped_column(sa.Numeric(10, 2), nullable=False)
    percentual: Mapped[Decimal] = mapped_column(sa.Numeric(5, 2), nullable=False, server_default="10.00")
    pago: Mapped[bool] = mapped_column(nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=sa.text("now()"))
