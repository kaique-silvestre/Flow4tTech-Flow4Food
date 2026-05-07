"""estoque e compras: compras, itens_compra, movimentos_estoque

Revision ID: 0005_estoque_compras
Revises: 0004_itens
Create Date: 2026-05-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_estoque_compras"
down_revision: Union[str, None] = "0004_itens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "compras",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fornecedor_id", sa.Integer(), sa.ForeignKey("fornecedores.id"), nullable=True),
        sa.Column("data_compra", sa.Date(), nullable=False),
        sa.Column("numero_nota", sa.String(50), nullable=True),
        sa.Column("total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "itens_compra",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("compra_id", sa.Integer(), sa.ForeignKey("compras.id"), nullable=False),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("itens.id"), nullable=False),
        sa.Column("quantidade", sa.Numeric(12, 4), nullable=False),
        sa.Column("custo_unitario", sa.Numeric(10, 4), nullable=False),
        sa.Column("custo_total", sa.Numeric(12, 2), nullable=False),
    )

    op.create_table(
        "movimentos_estoque",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("itens.id"), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("quantidade", sa.Numeric(12, 4), nullable=False),
        sa.Column("custo_unitario", sa.Numeric(10, 4), nullable=True),
        sa.Column("saldo_apos", sa.Numeric(12, 4), nullable=False),
        sa.Column("motivo", sa.String(30), nullable=True),
        sa.Column("observacao", sa.String(500), nullable=True),
        sa.Column("compra_id", sa.Integer(), sa.ForeignKey("compras.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("movimentos_estoque")
    op.drop_table("itens_compra")
    op.drop_table("compras")
