"""comandas, itens_comanda, eventos_comanda

Revision ID: 0006_comandas
Revises: 0005_estoque_compras
Create Date: 2026-05-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_comandas"
down_revision: Union[str, None] = "0005_estoque_compras"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "comandas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("identificacao", sa.String(150), nullable=False),
        sa.Column("tipo_identificacao", sa.String(10), nullable=False),
        sa.Column("garcom_id", sa.Integer(), sa.ForeignKey("garcons.id"), nullable=False),
        sa.Column("status", sa.String(15), nullable=False, server_default="aberta"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("pessoas", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "itens_comanda",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("comanda_id", sa.Integer(), sa.ForeignKey("comandas.id"), nullable=False),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("itens.id"), nullable=False),
        sa.Column("quantidade", sa.Numeric(10, 3), nullable=False),
        sa.Column("preco_unitario", sa.Numeric(10, 2), nullable=False),
        sa.Column("pessoa_associada", sa.String(100), nullable=True),
        sa.Column("observacao", sa.String(300), nullable=True),
        sa.Column("cortesia", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("cancelado", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("motivo_cancelamento", sa.String(30), nullable=True),
        sa.Column("estornado", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "eventos_comanda",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("comanda_id", sa.Integer(), sa.ForeignKey("comandas.id"), nullable=False),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column("garcom_id", sa.Integer(), sa.ForeignKey("garcons.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("eventos_comanda")
    op.drop_table("itens_comanda")
    op.drop_table("comandas")
