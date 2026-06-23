from __future__ import annotations

from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Assinatura(Base):
    __tablename__ = "assinaturas"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        sa.BigInteger(),
        sa.ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, server_default="trial")
    data_inicio: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("NOW()"))
    data_vencimento: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)  # noqa: UP045
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("NOW()"))


class AssinaturaHistory(Base):
    __tablename__ = "assinatura_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    assinatura_id: Mapped[int] = mapped_column(
        sa.Integer(),
        sa.ForeignKey("assinaturas.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_status: Mapped[Optional[str]] = mapped_column(sa.String(20), nullable=True)  # noqa: UP045
    to_status: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    changed_by: Mapped[Optional[int]] = mapped_column(sa.Integer(), nullable=True)  # noqa: UP045
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.text("NOW()"))
