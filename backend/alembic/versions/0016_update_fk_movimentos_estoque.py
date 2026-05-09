"""atualiza FK em movimentos_estoque: item_id → insumo_id (aponta para insumos)

Revision ID: 0016_update_fk_movimentos_estoque
Revises: 0015_update_fk_itens_comanda
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0016_fk_movimentos_estoque"
down_revision: Union[str, None] = "0015_update_fk_itens_comanda"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("movimentos_estoque") as batch_op:
        batch_op.alter_column("item_id", new_column_name="insumo_id")


def downgrade() -> None:
    with op.batch_alter_table("movimentos_estoque") as batch_op:
        batch_op.alter_column("insumo_id", new_column_name="item_id")
