from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Fornecedor(Base):
    __tablename__ = "fornecedores"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(nullable=False)
    telefone: Mapped[Optional[str]] = mapped_column(nullable=True)
    email: Mapped[Optional[str]] = mapped_column(nullable=True)
