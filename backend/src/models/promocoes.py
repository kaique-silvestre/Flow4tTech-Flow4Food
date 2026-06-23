import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Promocao(Base):
    __tablename__ = "promocoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        sa.BigInteger(),
        nullable=False,
        server_default=sa.text("(NULLIF(current_setting('app.tenant_id', true), ''))::bigint"),
    )
    nome: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(sa.Text(), nullable=True)  # noqa: UP045
    tipo_desconto: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    valor_desconto: Mapped[float] = mapped_column(sa.Numeric(10, 2), nullable=False)
    data_inicio: Mapped[datetime.date] = mapped_column(sa.Date(), nullable=False)
    data_fim: Mapped[Optional[datetime.date]] = mapped_column(sa.Date(), nullable=True)  # noqa: UP045
    hora_inicio: Mapped[Optional[datetime.time]] = mapped_column(sa.Time(), nullable=False, server_default="00:00:00")  # noqa: UP045
    hora_fim: Mapped[Optional[datetime.time]] = mapped_column(sa.Time(), nullable=False, server_default="23:59:59")  # noqa: UP045
    # PG column is INTEGER[]; SQLite tests use JSON fallback
    recorrencia: Mapped[str] = mapped_column(sa.String(10), nullable=False, server_default="nenhuma")
    dias_semana: Mapped[Optional[list]] = mapped_column(sa.ARRAY(sa.Integer()).with_variant(sa.JSON(), "sqlite"), nullable=True)  # noqa: UP045
    dias_mes: Mapped[Optional[list]] = mapped_column(sa.ARRAY(sa.Integer()).with_variant(sa.JSON(), "sqlite"), nullable=True)  # noqa: UP045
    criado_por: Mapped[Optional[int]] = mapped_column(  # noqa: UP045
        sa.BigInteger(),
        sa.ForeignKey("system_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(  # noqa: UP045
        sa.DateTime(timezone=True), server_default=sa.text("NOW()")
    )


class PromocaoProduto(Base):
    __tablename__ = "promocao_produtos"

    promocao_id: Mapped[int] = mapped_column(
        sa.BigInteger(),
        sa.ForeignKey("promocoes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    produto_id: Mapped[int] = mapped_column(sa.BigInteger(), primary_key=True)
