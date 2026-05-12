"""reset operational tables for unit-family model (UNI2)

Revision ID: 0020_reset_operational_tables
Revises: 0019_add_status_compras
Create Date: 2026-05-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0020_reset_operational_tables"
down_revision: Union[str, None] = "0019_add_status_compras"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Deletion order respects FK constraints
_OPERATIONAL_TABLES = [
    "pagamentos",
    "itens_comanda",
    "eventos_comanda",
    "comandas",
    "movimentos_estoque",
    "itens_compra",
    "compras",
    "ficha_tecnica",
    "insumos",
]


def upgrade() -> None:
    conn = op.get_bind()
    for table in _OPERATIONAL_TABLES:
        conn.execute(sa.text(f"DELETE FROM {table}"))  # noqa: S608


def downgrade() -> None:
    # Destructive migration — downgrade is intentionally a no-op
    pass
