"""add ativo to fornecedores

Revision ID: 0026_fornecedor_ativo
Revises: 0025_categoria_ativo
Create Date: 2026-05-12
"""

from alembic import op
import sqlalchemy as sa

revision = "0026_fornecedor_ativo"
down_revision = "0025_categoria_ativo"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "fornecedores",
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("fornecedores", "ativo")
