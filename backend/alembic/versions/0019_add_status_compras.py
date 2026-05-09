"""add status column to compras

Revision ID: 0019_add_status_compras
Revises: 0018_add_parent_id_categorias
Create Date: 2026-05-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0019_add_status_compras"
down_revision: Union[str, None] = "0018_add_parent_id_categorias"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "compras",
        sa.Column("status", sa.String(20), nullable=False, server_default="ativa"),
    )


def downgrade() -> None:
    op.drop_column("compras", "status")
