import enum

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class TipoPagamento(str, enum.Enum):
    DINHEIRO = "dinheiro"
    CREDITO = "credito"
    DEBITO = "debito"
    PIX = "pix"
    OUTRO = "outro"


class MetodoPagamento(Base):
    __tablename__ = "metodos_pagamento"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False, server_default=sa.text("(NULLIF(current_setting('app.tenant_id', true), ''))::bigint"))
    nome: Mapped[str] = mapped_column(nullable=False)
    ativo: Mapped[bool] = mapped_column(nullable=False, default=True)
    tipo: Mapped[str] = mapped_column(
        sa.String(),
        nullable=False,
        server_default="outro",
    )
    padrao: Mapped[bool] = mapped_column(nullable=False, default=False)
