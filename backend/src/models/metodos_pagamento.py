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
    nome: Mapped[str] = mapped_column(nullable=False, unique=True)
    ativo: Mapped[bool] = mapped_column(nullable=False, default=True)
    tipo: Mapped[str] = mapped_column(
        sa.String(),
        nullable=False,
        server_default="outro",
    )
    padrao: Mapped[bool] = mapped_column(nullable=False, default=False)
