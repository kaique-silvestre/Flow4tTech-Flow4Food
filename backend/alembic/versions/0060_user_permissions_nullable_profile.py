"""user_permissions table + profile_id nullable

Revision ID: 0060
Revises: 0059
"""

from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0060"
down_revision: Union[str, None] = "0059"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    is_pg = conn.dialect.name == "postgresql"

    op.create_table(
        "user_permissions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("system_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("screen", sa.String(50), nullable=False),
        sa.Column("can_access", sa.Boolean(), nullable=False, server_default="true"),
        sa.UniqueConstraint("user_id", "screen", name="uq_user_permissions_user_screen"),
    )

    op.alter_column("system_users", "profile_id", nullable=True)

    if is_pg:
        conn.execute(sa.text("ALTER TABLE user_permissions ENABLE ROW LEVEL SECURITY"))
        conn.execute(sa.text(
            "CREATE POLICY tenant_isolation ON user_permissions "
            "USING (tenant_id = (NULLIF(current_setting('app.tenant_id', true), ''))::bigint)"
        ))


def downgrade() -> None:
    conn = op.get_bind()
    is_pg = conn.dialect.name == "postgresql"

    if is_pg:
        conn.execute(sa.text("DROP POLICY IF EXISTS tenant_isolation ON user_permissions"))

    op.alter_column("system_users", "profile_id", nullable=False)
    op.drop_table("user_permissions")
