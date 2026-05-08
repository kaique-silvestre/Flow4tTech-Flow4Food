"""pagamentos + colunas fechamento em comandas

Revision ID: 0007_fechamento
Revises: 0006_comandas
Create Date: 2026-05-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_fechamento"
down_revision: Union[str, None] = "0006_comandas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("comandas", sa.Column("desconto_percentual", sa.Numeric(5, 2), nullable=True))
    op.add_column("comandas", sa.Column("desconto_valor", sa.Numeric(10, 2), nullable=True))
    op.add_column("comandas", sa.Column("total", sa.Numeric(10, 2), nullable=True))
    op.add_column("comandas", sa.Column("saldo_pendente", sa.Numeric(10, 2), nullable=True))
    op.add_column("comandas", sa.Column("data_fechamento", sa.DateTime(), nullable=True))

    op.create_table(
        "pagamentos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("comanda_id", sa.Integer(), sa.ForeignKey("comandas.id"), nullable=False),
        sa.Column("metodo_id", sa.Integer(), sa.ForeignKey("metodos_pagamento.id"), nullable=False),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("pagamentos")
    op.drop_column("comandas", "data_fechamento")
    op.drop_column("comandas", "saldo_pendente")
    op.drop_column("comandas", "total")
    op.drop_column("comandas", "desconto_valor")
    op.drop_column("comandas", "desconto_percentual")
