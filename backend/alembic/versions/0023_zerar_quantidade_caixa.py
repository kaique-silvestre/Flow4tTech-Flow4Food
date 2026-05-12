"""zera quantidade_caixa em todos os insumos

Revision ID: 0023_zerar_quantidade_caixa
Revises: 0022_fix_unidade_base_legado
Create Date: 2026-05-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0023_zerar_quantidade_caixa"
down_revision: Union[str, None] = "0022_fix_unidade_base_legado"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE insumos SET quantidade_caixa = NULL"))


def downgrade() -> None:
    pass
