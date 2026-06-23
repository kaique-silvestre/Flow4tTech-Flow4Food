"""grant app_user permissions on tables created after migration 0050

Revision ID: 0064
Revises: 0063
Create Date: 2026-06-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0064"
down_revision: Union[str, None] = "0063"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RW_TABLES = [
    "tenant_eventos",
    "promocoes",
    "promocao_produtos",
    "user_permissions",
]

_SEQUENCES = [
    "tenant_eventos_id_seq",
    "promocoes_id_seq",
    "user_permissions_id_seq",
]


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    for table in _RW_TABLES:
        conn.execute(sa.text(
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {table} TO app_user"
        ))

    for seq in _SEQUENCES:
        conn.execute(sa.text(
            f"GRANT USAGE, SELECT ON SEQUENCE {seq} TO app_user"
        ))

    # view_calendario_consolidado — SELECT only
    conn.execute(sa.text(
        "GRANT SELECT ON view_calendario_consolidado TO app_user"
    ))


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    for table in _RW_TABLES:
        conn.execute(sa.text(f"REVOKE ALL ON TABLE {table} FROM app_user"))

    for seq in _SEQUENCES:
        conn.execute(sa.text(f"REVOKE ALL ON SEQUENCE {seq} FROM app_user"))

    conn.execute(sa.text("REVOKE ALL ON view_calendario_consolidado FROM app_user"))
