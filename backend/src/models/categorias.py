from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(sa.BigInteger(), nullable=False, server_default=sa.text("(NULLIF(current_setting('app.tenant_id', true), ''))::bigint"))
    nome: Mapped[str] = mapped_column(nullable=False, unique=True)
    parent_id: Mapped[Optional[int]] = mapped_column(sa.Integer(), nullable=True)
    ativo: Mapped[bool] = mapped_column(nullable=False, server_default=sa.true())
