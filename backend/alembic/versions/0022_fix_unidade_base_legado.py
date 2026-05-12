"""fix unidade_base legado — remapeia MILILITRO/LITRO para UNIDADE

Revision ID: 0022_fix_unidade_base_legado
Revises: 0021_unique_insumo_nome
Create Date: 2026-05-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0022_fix_unidade_base_legado"
down_revision: Union[str, None] = "0021_unique_insumo_nome"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE insumos SET unidade_base = 'UNIDADE' WHERE unidade_base IN ('MILILITRO', 'LITRO')"
    ))


def downgrade() -> None:
    pass
