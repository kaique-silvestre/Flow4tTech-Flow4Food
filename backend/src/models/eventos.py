from __future__ import annotations

import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class TenantEvento(Base):
    __tablename__ = "tenant_eventos"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        sa.BigInteger(),
        nullable=False,
        server_default=sa.text("(NULLIF(current_setting('app.tenant_id', true), ''))::bigint"),
    )
    titulo: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(sa.Text(), nullable=True)  # noqa: UP045
    data_evento: Mapped[datetime.date] = mapped_column(sa.Date(), nullable=False)
    criado_por: Mapped[Optional[int]] = mapped_column(  # noqa: UP045
        sa.BigInteger(),
        sa.ForeignKey("system_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(  # noqa: UP045
        sa.DateTime(timezone=True), server_default=sa.text("NOW()")
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(  # noqa: UP045
        sa.DateTime(timezone=True), server_default=sa.text("NOW()")
    )
