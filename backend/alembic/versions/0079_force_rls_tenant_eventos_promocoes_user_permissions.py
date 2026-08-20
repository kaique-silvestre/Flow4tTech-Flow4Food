"""force RLS on tenant_eventos, promocoes and user_permissions

Revision ID: 0079
Revises: 0078
Create Date: 2026-08-20

Without FORCE ROW LEVEL SECURITY the table owner (matchpoint) bypasses all
RLS policies, leaking every tenant's rows to every other tenant.

Migrations 0058, 0059 and 0060 enabled RLS on tenant_eventos, promocoes
and user_permissions respectively but forgot to also FORCE it, leaving
them vulnerable to the same bug class fixed retroactively for 23 earlier
tables in migration 0049.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0079"
down_revision: Union[str, None] = "0078"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RLS_TABLES = [
    "tenant_eventos",
    "promocoes",
    "user_permissions",
]


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    for table in _RLS_TABLES:
        bind.execute(sa.text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    for table in _RLS_TABLES:
        bind.execute(sa.text(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY"))
