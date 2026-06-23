"""force RLS and fix tenant_id default on itens_consumo_interno

Revision ID: 0054
Revises: 0053
Create Date: 2026-06-04

Migration 0052 used ENABLE ROW LEVEL SECURITY but missed FORCE ROW LEVEL
SECURITY, allowing the table owner to bypass RLS.  Also aligns the
tenant_id column default with the pattern established in migration 0049.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0054"
down_revision: Union[str, None] = "0053"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TENANT_DEFAULT_EXPR = (
    "(NULLIF(current_setting('app.tenant_id', true), ''))::bigint"
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    bind.execute(sa.text("ALTER TABLE itens_consumo_interno FORCE ROW LEVEL SECURITY"))
    bind.execute(
        sa.text(
            f"ALTER TABLE itens_consumo_interno "
            f"ALTER COLUMN tenant_id SET DEFAULT {_TENANT_DEFAULT_EXPR}"
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    bind.execute(sa.text("ALTER TABLE itens_consumo_interno NO FORCE ROW LEVEL SECURITY"))
    bind.execute(
        sa.text("ALTER TABLE itens_consumo_interno ALTER COLUMN tenant_id SET DEFAULT 1")
    )
