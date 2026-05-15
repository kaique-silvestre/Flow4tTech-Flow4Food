"""add nivel_critico to insumos

Revision ID: 0031
Revises: 0030
Create Date: 2026-05-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0031"
down_revision: Union[str, None] = "0030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "insumos",
        sa.Column("nivel_critico", sa.Numeric(12, 4), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("insumos", "nivel_critico")
