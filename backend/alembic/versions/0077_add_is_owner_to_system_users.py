"""add_is_owner_to_system_users

Revision ID: 0077
Revises: 0076
Create Date: 2026-06-15

"""
from alembic import op
import sqlalchemy as sa

revision = '0077'
down_revision = '0076'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'system_users',
        sa.Column('is_owner', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    op.drop_column('system_users', 'is_owner')
