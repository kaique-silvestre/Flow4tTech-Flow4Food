"""extend compras for scheduled purchases

Revision ID: 0035a
Revises: 0034a
Create Date: 2026-05-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0035a"
down_revision: Union[str, None] = "0034a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("compras", sa.Column("tipo_compra", sa.String(20), nullable=False, server_default="imediata"))
    op.add_column("compras", sa.Column("data_prevista_recebimento", sa.Date(), nullable=True))
    op.add_column("compras", sa.Column("data_real_recebimento", sa.Date(), nullable=True))
    op.add_column("compras", sa.Column("data_prevista_pagamento", sa.Date(), nullable=True))

    conn = op.get_bind()
    conn.execute(sa.text("UPDATE compras SET status = 'recebido' WHERE status = 'ativa'"))
    conn.execute(sa.text("UPDATE compras SET status = 'cancelado' WHERE status = 'cancelada'"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE compras SET status = 'ativa' WHERE status IN ('recebido', 'pago')"))
    conn.execute(sa.text("UPDATE compras SET status = 'cancelada' WHERE status = 'cancelado'"))

    op.drop_column("compras", "data_prevista_pagamento")
    op.drop_column("compras", "data_real_recebimento")
    op.drop_column("compras", "data_prevista_recebimento")
    op.drop_column("compras", "tipo_compra")
