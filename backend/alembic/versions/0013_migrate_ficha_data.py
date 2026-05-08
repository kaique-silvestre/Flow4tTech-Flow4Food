"""migra fichas_tecnicas + componentes_ficha para ficha_tecnica flat

Revision ID: 0013_migrate_ficha_data
Revises: 0012_migrate_itens_data
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013_migrate_ficha_data"
down_revision: Union[str, None] = "0012_migrate_itens_data"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    # Flat join: fichas_tecnicas.item_composto_id → produto_id; componentes_ficha.insumo_id → insumo_id
    conn.execute(sa.text("""
        INSERT INTO ficha_tecnica (produto_id, insumo_id, quantidade)
        SELECT ft.item_composto_id, cf.insumo_id, cf.quantidade
        FROM componentes_ficha cf
        JOIN fichas_tecnicas ft ON cf.ficha_tecnica_id = ft.id
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM ficha_tecnica"))
