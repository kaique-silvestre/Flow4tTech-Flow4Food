"""cria tabela insumos

Revision ID: 0009_create_insumos
Revises: 0008_estabelecimento
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_create_insumos"
down_revision: Union[str, None] = "0008_estabelecimento"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "insumos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("categoria_id", sa.Integer(), sa.ForeignKey("categorias.id"), nullable=True),
        sa.Column("unidade_base", sa.String(10), nullable=False, server_default="un"),
        sa.Column("quantidade_caixa", sa.Integer(), nullable=True),
        sa.Column("custo_medio", sa.Numeric(10, 4), nullable=True),
        sa.Column("estoque_atual", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default="true"),
    )


def downgrade() -> None:
    op.drop_table("insumos")
