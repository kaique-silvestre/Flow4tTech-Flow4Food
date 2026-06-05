from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Estabelecimento(Base):
    __tablename__ = "estabelecimento"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False, server_default=sa.text("(NULLIF(current_setting('app.tenant_id', true), ''))::bigint"))
    nome: Mapped[str] = mapped_column(sa.String(200), nullable=False, default="Estabelecimento")
    cnpj: Mapped[Optional[str]] = mapped_column(sa.String(20), nullable=True)
    endereco: Mapped[Optional[str]] = mapped_column(sa.String(300), nullable=True)
    telefone: Mapped[Optional[str]] = mapped_column(sa.String(30), nullable=True)
