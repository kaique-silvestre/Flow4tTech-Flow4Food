"""add estornado (soft-delete) flag to itens_consumo_interno

Revision ID: 0086
Revises: 0085
Create Date: 2026-08-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0086"
down_revision: Union[str, None] = "0085"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "itens_consumo_interno",
        sa.Column("estornado", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "itens_consumo_interno",
        sa.Column("estornado_em", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("itens_consumo_interno", "estornado_em")
    op.drop_column("itens_consumo_interno", "estornado")
