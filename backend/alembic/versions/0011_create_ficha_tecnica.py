"""cria tabela ficha_tecnica (flat)

Revision ID: 0011_create_ficha_tecnica
Revises: 0010_create_produtos
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_create_ficha_tecnica"
down_revision: Union[str, None] = "0010_create_produtos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ficha_tecnica",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("produto_id", sa.Integer(), sa.ForeignKey("produtos.id"), nullable=False),
        sa.Column("insumo_id", sa.Integer(), sa.ForeignKey("insumos.id"), nullable=False),
        sa.Column("quantidade", sa.Numeric(10, 4), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ficha_tecnica")
