"""atualiza FK em itens_comanda: item_id → produto_id (aponta para produtos)

Revision ID: 0015_update_fk_itens_comanda
Revises: 0014_update_fk_compras
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0015_update_fk_itens_comanda"
down_revision: Union[str, None] = "0014_update_fk_compras"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("itens_comanda") as batch_op:
        batch_op.alter_column("item_id", new_column_name="produto_id")


def downgrade() -> None:
    with op.batch_alter_table("itens_comanda") as batch_op:
        batch_op.alter_column("produto_id", new_column_name="item_id")
