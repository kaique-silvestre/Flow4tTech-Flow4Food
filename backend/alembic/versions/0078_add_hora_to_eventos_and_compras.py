"""add hora to tenant_eventos and compras

Revision ID: 0078
Revises: 0077
Create Date: 2026-06-15

"""
from alembic import op
import sqlalchemy as sa

revision = "0078"
down_revision = "0076"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenant_eventos", sa.Column("hora_inicio", sa.Time(), nullable=True))
    op.add_column("tenant_eventos", sa.Column("hora_fim", sa.Time(), nullable=True))
    op.add_column("compras", sa.Column("hora_prevista_recebimento", sa.Time(), nullable=True))


def downgrade() -> None:
    op.drop_column("tenant_eventos", "hora_inicio")
    op.drop_column("tenant_eventos", "hora_fim")
    op.drop_column("compras", "hora_prevista_recebimento")
