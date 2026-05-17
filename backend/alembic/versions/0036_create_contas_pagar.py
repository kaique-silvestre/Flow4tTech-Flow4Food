"""create contas_pagar and notificacoes tables

Revision ID: 0036
Revises: 0035
Create Date: 2026-05-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0036"
down_revision: Union[str, None] = "0035"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contas_pagar",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("compra_id", sa.Integer(), sa.ForeignKey("compras.id"), nullable=True),
        sa.Column("fornecedor_id", sa.Integer(), sa.ForeignKey("fornecedores.id"), nullable=True),
        sa.Column("valor", sa.Numeric(12, 2), nullable=False),
        sa.Column("data_vencimento", sa.Date(), nullable=False),
        sa.Column("data_pagamento", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pendente"),
        sa.Column("metodo_pagamento_id", sa.Integer(), sa.ForeignKey("metodos_pagamento.id"), nullable=True),
        sa.Column("observacao", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_contas_pagar_status", "contas_pagar", ["status"])
    op.create_index("ix_contas_pagar_data_vencimento", "contas_pagar", ["data_vencimento"])
    op.create_index("ix_contas_pagar_compra_id", "contas_pagar", ["compra_id"])

    op.create_table(
        "notificacoes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo", sa.String(50), nullable=False),
        sa.Column("referencia_id", sa.Integer(), nullable=True),
        sa.Column("mensagem", sa.String(500), nullable=False),
        sa.Column("lida", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_notificacoes_lida", "notificacoes", ["lida"])


def downgrade() -> None:
    op.drop_index("ix_notificacoes_lida", "notificacoes")
    op.drop_table("notificacoes")
    op.drop_index("ix_contas_pagar_compra_id", "contas_pagar")
    op.drop_index("ix_contas_pagar_data_vencimento", "contas_pagar")
    op.drop_index("ix_contas_pagar_status", "contas_pagar")
    op.drop_table("contas_pagar")
