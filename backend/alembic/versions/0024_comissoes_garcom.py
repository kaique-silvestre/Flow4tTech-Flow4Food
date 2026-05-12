"""cria tabela comissoes_garcom

Revision ID: 0024_comissoes_garcom
Revises: 0023_zerar_quantidade_caixa
Create Date: 2026-05-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0024_comissoes_garcom"
down_revision: Union[str, None] = "0023_zerar_quantidade_caixa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "comissoes_garcom",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("garcom_id", sa.Integer(), nullable=False),
        sa.Column("comanda_id", sa.Integer(), nullable=False),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column("percentual", sa.Numeric(5, 2), nullable=False, server_default="10.00"),
        sa.Column("pago", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["garcom_id"], ["garcons.id"]),
        sa.ForeignKeyConstraint(["comanda_id"], ["comandas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("comissoes_garcom")
