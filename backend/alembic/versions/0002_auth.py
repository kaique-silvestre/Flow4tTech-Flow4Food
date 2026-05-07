"""auth: config_seguranca table

Revision ID: 0002_auth
Revises: 0001_initial_empty
Create Date: 2026-05-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_auth"
down_revision: Union[str, None] = "0001_initial_empty"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "config_seguranca",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("senha_hash", sa.String, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("config_seguranca")
