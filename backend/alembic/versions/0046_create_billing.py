"""create planos and pagamentos_assinatura tables

Revision ID: 0046
Revises: 0045
Create Date: 2026-05-28

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0046"
down_revision: Union[str, None] = "0045"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "planos",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("preco_mensal", sa.Numeric(10, 2), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    op.create_table(
        "pagamentos_assinatura",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.BigInteger(),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column("data_pagamento", sa.Date(), nullable=False),
        sa.Column("data_vencimento", sa.Date(), nullable=True),
        sa.Column("gateway_ref", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_pagamentos_assinatura_tenant_id", "pagamentos_assinatura", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_pagamentos_assinatura_tenant_id", "pagamentos_assinatura")
    op.drop_table("pagamentos_assinatura")
    op.drop_table("planos")
