"""add estoque_reservado to insumos

Revision ID: 0029
Revises: 0028
Create Date: 2026-05-13

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0029_estoque_reservado"
down_revision: Union[str, None] = "0028_add_troco_pagamento"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "insumos",
        sa.Column(
            "estoque_reservado",
            sa.Numeric(12, 4),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("insumos", "estoque_reservado")
