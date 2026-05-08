"""migra dados de itens para insumos e produtos

Revision ID: 0012_migrate_itens_data
Revises: 0011_create_ficha_tecnica
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012_migrate_itens_data"
down_revision: Union[str, None] = "0011_create_ficha_tecnica"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    # itens onde vendavel=false → insumos (preserva IDs)
    conn.execute(sa.text("""
        INSERT INTO insumos (id, nome, categoria_id, unidade_base, quantidade_caixa, custo_medio, estoque_atual, ativo)
        SELECT id, nome, categoria_id, unidade_base, quantidade_caixa, custo_medio, estoque_atual, ativo
        FROM itens
        WHERE vendavel = false OR vendavel = 0
    """))
    # itens onde vendavel=true → produtos (preserva IDs)
    conn.execute(sa.text("""
        INSERT INTO produtos (id, nome, categoria_id, preco_venda, ativo)
        SELECT id, nome, categoria_id, preco_venda, ativo
        FROM itens
        WHERE vendavel = true OR vendavel = 1
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM produtos"))
    conn.execute(sa.text("DELETE FROM insumos"))
