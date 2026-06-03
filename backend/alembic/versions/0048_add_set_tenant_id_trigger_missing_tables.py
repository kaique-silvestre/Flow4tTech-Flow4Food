"""add set_tenant_id trigger to tables missing it

Revision ID: 0048
Revises: 0047
Create Date: 2026-05-29

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0048"
down_revision: Union[str, None] = "0047"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = [
    "garcons",
    "metodos_pagamento",
    "contas_pagar",
    "notificacoes",
    "estabelecimento",
    "ficha_tecnica",
    "itens_compra",
]


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    for table in _TABLES:
        bind.execute(sa.text(
            f"CREATE TRIGGER trg_set_tenant_id "
            f"BEFORE INSERT ON {table} "
            f"FOR EACH ROW EXECUTE FUNCTION set_tenant_id()"
        ))


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    for table in _TABLES:
        bind.execute(sa.text(f"DROP TRIGGER IF EXISTS trg_set_tenant_id ON {table}"))
