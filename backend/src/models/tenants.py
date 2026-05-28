from __future__ import annotations

from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(sa.BigInteger(), primary_key=True)
    nome_fantasia: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    cnpj: Mapped[Optional[str]] = mapped_column(sa.String(18), nullable=True, unique=True)  # noqa: UP045
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, server_default="ativo")
    admin_user_id: Mapped[Optional[int]] = mapped_column(nullable=True)  # noqa: UP045
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("NOW()"))
