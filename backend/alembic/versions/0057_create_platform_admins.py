"""platform_admins: tabela global sem RLS para admins da plataforma

Revision ID: 0057
Revises: 0056
"""

from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0057"
down_revision: Union[str, None] = "0056"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_admins",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("password_hash", sa.String(200), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("email", name="uq_platform_admins_email"),
    )


def downgrade() -> None:
    op.drop_table("platform_admins")
