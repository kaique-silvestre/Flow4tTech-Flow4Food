"""add cnpj to fornecedores

Revision ID: 0070
Revises: 0069
Create Date: 2026-06-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0070"
down_revision: Union[str, None] = "0069"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("fornecedores", sa.Column("cnpj", sa.String(14), nullable=True))


def downgrade() -> None:
    op.drop_column("fornecedores", "cnpj")
