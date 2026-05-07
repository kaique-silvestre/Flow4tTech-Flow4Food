from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class MetodoPagamento(Base):
    __tablename__ = "metodos_pagamento"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(nullable=False, unique=True)
    ativo: Mapped[bool] = mapped_column(nullable=False, default=True)
