"""platform_announcements: comunicados broadcast e direcionados

Revision ID: 0073
Revises: 0072
"""

from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0073"
down_revision: Union[str, None] = "0072"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_announcements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("target", sa.String(20), nullable=False, server_default="all"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_table(
        "announcement_targets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("announcement_id", sa.Integer(), sa.ForeignKey("platform_announcements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
    )
    op.create_table(
        "announcement_reads",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("announcement_id", sa.Integer(), sa.ForeignKey("platform_announcements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("announcement_id", "user_id", name="uq_announcement_reads"),
    )


def downgrade() -> None:
    op.drop_table("announcement_reads")
    op.drop_table("announcement_targets")
    op.drop_table("platform_announcements")
