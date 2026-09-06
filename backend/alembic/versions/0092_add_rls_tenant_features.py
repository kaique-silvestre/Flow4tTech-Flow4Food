"""add RLS to tenant_features

Revision ID: 0092
Revises: 0091
Create Date: 2026-09-06

tenant_features (created in migration 0074) never got RLS enabled, unlike
every other tenant-scoped table (pattern established in 0043/0047, FORCE
added retroactively in 0049/0054/0079, most recent example in 0081).
Feature-flag rows are per-tenant and were relying solely on the
`tenant_id` filter applied in application code (`require_feature` in
api/dependencies.py) for isolation — this adds defense-in-depth at the
database layer.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0092"
down_revision: Union[str, None] = "0091"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TENANT_ID_EXPR = "NULLIF(current_setting('app.tenant_id', true), '')::bigint"


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    bind.execute(sa.text("ALTER TABLE tenant_features ENABLE ROW LEVEL SECURITY"))
    bind.execute(sa.text("ALTER TABLE tenant_features FORCE ROW LEVEL SECURITY"))
    bind.execute(
        sa.text(
            "CREATE POLICY tenant_isolation ON tenant_features "
            f"USING (tenant_id = {_TENANT_ID_EXPR}) "
            f"WITH CHECK (tenant_id = {_TENANT_ID_EXPR})"
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    bind.execute(sa.text("DROP POLICY IF EXISTS tenant_isolation ON tenant_features"))
    bind.execute(sa.text("ALTER TABLE tenant_features NO FORCE ROW LEVEL SECURITY"))
    bind.execute(sa.text("ALTER TABLE tenant_features DISABLE ROW LEVEL SECURITY"))
