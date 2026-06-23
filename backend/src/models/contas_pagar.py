import datetime
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ContaPagar(Base):
    __tablename__ = "contas_pagar"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False, server_default=sa.text("(NULLIF(current_setting('app.tenant_id', true), ''))::bigint"))
    compra_id: Mapped[Optional[int]] = mapped_column(sa.ForeignKey("compras.id"), nullable=True)
    fornecedor_id: Mapped[Optional[int]] = mapped_column(sa.ForeignKey("fornecedores.id"), nullable=True)
    valor: Mapped[Decimal] = mapped_column(sa.Numeric(12, 2), nullable=False)
    data_vencimento: Mapped[datetime.date] = mapped_column(sa.Date(), nullable=False)
    data_pagamento: Mapped[Optional[datetime.date]] = mapped_column(sa.Date(), nullable=True)
    # status: pendente | pago | vencido | cancelado
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, server_default="pendente")
    metodo_pagamento_id: Mapped[Optional[int]] = mapped_column(
        sa.ForeignKey("metodos_pagamento.id"), nullable=True
    )
    observacao: Mapped[Optional[str]] = mapped_column(sa.String(500), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(), nullable=False, server_default=sa.func.now()
    )


class Notificacao(Base):
    __tablename__ = "notificacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False, server_default=sa.text("(NULLIF(current_setting('app.tenant_id', true), ''))::bigint"))
    tipo: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    referencia_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    mensagem: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    lida: Mapped[bool] = mapped_column(sa.Boolean(), nullable=False, server_default="false")
    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime(), nullable=False, server_default=sa.func.now()
    )
