"""tabela estabelecimento

Revision ID: 0008_estabelecimento
Revises: 0007_fechamento
Create Date: 2026-05-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_estabelecimento"
down_revision: Union[str, None] = "0007_fechamento"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "estabelecimento",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(200), nullable=False, server_default="Estabelecimento"),
        sa.Column("cnpj", sa.String(20), nullable=True),
        sa.Column("endereco", sa.String(300), nullable=True),
        sa.Column("telefone", sa.String(30), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("estabelecimento")
