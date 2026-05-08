"""atualiza FK em itens_compra: item_id → insumo_id (aponta para insumos)

Revision ID: 0014_update_fk_compras
Revises: 0013_migrate_ficha_data
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0014_update_fk_compras"
down_revision: Union[str, None] = "0013_migrate_ficha_data"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("itens_compra") as batch_op:
        batch_op.alter_column("item_id", new_column_name="insumo_id")


def downgrade() -> None:
    with op.batch_alter_table("itens_compra") as batch_op:
        batch_op.alter_column("insumo_id", new_column_name="item_id")
