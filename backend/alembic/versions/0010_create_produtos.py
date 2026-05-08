"""cria tabela produtos

Revision ID: 0010_create_produtos
Revises: 0009_create_insumos
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010_create_produtos"
down_revision: Union[str, None] = "0009_create_insumos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "produtos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("categoria_id", sa.Integer(), sa.ForeignKey("categorias.id"), nullable=True),
        sa.Column("preco_venda", sa.Numeric(10, 2), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default="true"),
    )


def downgrade() -> None:
    op.drop_table("produtos")
