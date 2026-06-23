"""create platform_settings

Revision ID: 0072
Revises: 0071
Create Date: 2026-06-13

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0072"
down_revision: Union[str, None] = "0071"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "platform_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.String(500), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.execute(
        "INSERT INTO platform_settings (key, value) VALUES ('trial_duration_days', '14')"
    )
    op.execute(
        "INSERT INTO platform_settings (key, value) VALUES ('contact_email', 'contato@flow4tech.com.br')"
    )


def downgrade() -> None:
    op.drop_table("platform_settings")
