"""create audit_logs

Revision ID: 0076
Revises: 0075
Create Date: 2026-06-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0076"
down_revision: Union[str, None] = "0075"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity", sa.String(100), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("before_data", sa.Text(), nullable=True),
        sa.Column("after_data", sa.Text(), nullable=True),
        sa.Column("impersonated_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )

    if is_pg:
        op.execute("ALTER TABLE audit_logs ALTER COLUMN before_data TYPE jsonb USING before_data::jsonb")
        op.execute("ALTER TABLE audit_logs ALTER COLUMN after_data TYPE jsonb USING after_data::jsonb")


def downgrade() -> None:
    op.drop_table("audit_logs")
