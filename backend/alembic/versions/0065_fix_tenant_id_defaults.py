"""fix tenant_id server_default on tenant_eventos, promocoes, user_permissions

Revision ID: 0065
Revises: 0064
Create Date: 2026-06-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0065"
down_revision: Union[str, None] = "0064"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TENANT_DEFAULT = "(NULLIF(current_setting('app.tenant_id', true), ''))::bigint"
_TABLES = ["tenant_eventos", "promocoes", "user_permissions"]


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return
    for table in _TABLES:
        conn.execute(sa.text(
            f"ALTER TABLE {table} ALTER COLUMN tenant_id SET DEFAULT {_TENANT_DEFAULT}"
        ))


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return
    for table in _TABLES:
        conn.execute(sa.text(
            f"ALTER TABLE {table} ALTER COLUMN tenant_id DROP DEFAULT"
        ))
