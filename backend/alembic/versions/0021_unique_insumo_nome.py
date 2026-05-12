"""add unique constraint on insumos.nome

Revision ID: 0021_unique_insumo_nome
Revises: 0020_reset_operational_tables
Create Date: 2026-05-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0021_unique_insumo_nome"
down_revision: Union[str, None] = "0020_reset_operational_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    # Remove duplicate insumos, keeping the one with the lowest id per name
    conn.execute(sa.text("""
        DELETE FROM insumos
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM insumos
            GROUP BY nome
        )
    """))
    op.create_index("ix_insumos_nome_unique", "insumos", ["nome"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_insumos_nome_unique", table_name="insumos")
