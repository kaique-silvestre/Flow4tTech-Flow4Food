"""remove tabelas itens, fichas_tecnicas, componentes_ficha

Revision ID: 0017_drop_old_tables
Revises: 0016_update_fk_movimentos_estoque
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0017_drop_old_tables"
down_revision: Union[str, None] = "0016_update_fk_movimentos_estoque"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("componentes_ficha")
    op.drop_table("fichas_tecnicas")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Postgres: itens_compra/itens_comanda/movimentos_estoque still hold FK
        # constraints pointing to itens (column was renamed but FK was not dropped).
        # CASCADE removes those dangling constraints automatically.
        op.execute("DROP TABLE itens CASCADE")
    else:
        op.drop_table("itens")


def downgrade() -> None:
    op.create_table(
        "itens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("categoria_id", sa.Integer(), sa.ForeignKey("categorias.id"), nullable=True),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("vendavel", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("unidade_base", sa.String(), nullable=False),
        sa.Column("quantidade_caixa", sa.Integer(), nullable=True),
        sa.Column("custo_medio", sa.Numeric(10, 4), nullable=True),
        sa.Column("preco_venda", sa.Numeric(10, 2), nullable=True),
        sa.Column("estoque_atual", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_table(
        "fichas_tecnicas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_composto_id", sa.Integer(), sa.ForeignKey("itens.id"), nullable=False, unique=True),
    )
    op.create_table(
        "componentes_ficha",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ficha_tecnica_id", sa.Integer(), sa.ForeignKey("fichas_tecnicas.id"), nullable=False),
        sa.Column("insumo_id", sa.Integer(), sa.ForeignKey("itens.id"), nullable=False),
        sa.Column("quantidade", sa.Numeric(10, 4), nullable=False),
    )
