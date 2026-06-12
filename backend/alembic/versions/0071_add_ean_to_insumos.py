"""add ean to insumos

Revision ID: 0071
Revises: 0070
Create Date: 2026-06-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0071"
down_revision: Union[str, None] = "0070"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("insumos", sa.Column("ean", sa.String(14), nullable=True))


def downgrade() -> None:
    op.drop_column("insumos", "ean")
