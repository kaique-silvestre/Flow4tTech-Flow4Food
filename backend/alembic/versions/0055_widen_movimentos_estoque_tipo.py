"""widen movimentos_estoque.tipo to VARCHAR(30)

saida_consumo_interno = 21 chars, original column was VARCHAR(20).

Revision ID: 0055
Revises: 0054
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0055"
down_revision: Union[str, None] = "0054"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "movimentos_estoque",
        "tipo",
        existing_type=sa.String(20),
        type_=sa.String(30),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "movimentos_estoque",
        "tipo",
        existing_type=sa.String(30),
        type_=sa.String(20),
        existing_nullable=False,
    )
