"""RBAC: profiles, permissions, users, password_resets

Revision ID: 0034
Revises: 0033
Create Date: 2026-05-17

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0034"
down_revision: Union[str, None] = "0033"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCREENS = ("dashboard", "comandas", "compras", "estoque", "cadastros", "relatorios", "configuracoes", "gestao_usuarios")


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(300), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_profiles_tenant_id", "profiles", ["tenant_id"])

    op.create_table(
        "profile_permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("screen", sa.String(50), nullable=False),
        sa.Column("can_access", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.CheckConstraint(f"screen IN {SCREENS!r}", name="ck_permission_screen"),
    )
    op.create_index("ix_profile_permissions_profile_id", "profile_permissions", ["profile_id"])

    op.create_table(
        "system_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("profiles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("email", sa.String(254), nullable=True),
        sa.Column("password_hash", sa.String(200), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "username", name="uq_system_users_tenant_username"),
    )
    op.create_index("ix_system_users_tenant_id", "system_users", ["tenant_id"])
    op.create_index("ix_system_users_email", "system_users", ["email"], unique=True)

    op.create_table(
        "password_resets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("system_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(100), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_password_resets_token", "password_resets", ["token"])


def downgrade() -> None:
    op.drop_table("password_resets")
    op.drop_table("system_users")
    op.drop_table("profile_permissions")
    op.drop_table("profiles")
