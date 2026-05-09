"""add parent_id to categorias (subcategorias 2 niveis)

Revision ID: 0018_add_parent_id_categorias
Revises: 0017_drop_old_tables
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0018_add_parent_id_categorias"
down_revision: Union[str, None] = "0017_drop_old_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("categorias", sa.Column("parent_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("categorias", "parent_id")
