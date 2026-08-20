"""add RLS to permission_templates and template_permissions

Revision ID: 0081
Revises: 0080
Create Date: 2026-08-20

permission_templates and template_permissions never got RLS, unlike every
other tenant table (RLS added in 0043/0047, FORCE added retroactively in
0054/0079). The repository-level filter in get_template_by_id was the only
protection; this adds defense-in-depth at the database layer.

permission_templates rows may be system templates (is_system=true,
tenant_id NULL) which are visible to every tenant but never owned/writable
by one, so the policy allows read of system rows while restricting writes
to the owning tenant's custom rows. template_permissions has no tenant_id
of its own — its visibility is derived via EXISTS against
permission_templates through template_id.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0081"
down_revision: Union[str, None] = "0080"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TENANT_ID_EXPR = "NULLIF(current_setting('app.tenant_id', true), '')::bigint"


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    bind.execute(sa.text("ALTER TABLE permission_templates ENABLE ROW LEVEL SECURITY"))
    bind.execute(sa.text("ALTER TABLE permission_templates FORCE ROW LEVEL SECURITY"))
    bind.execute(
        sa.text(
            "CREATE POLICY tenant_isolation ON permission_templates "
            f"USING (is_system OR tenant_id = {_TENANT_ID_EXPR}) "
            f"WITH CHECK (NOT is_system AND tenant_id = {_TENANT_ID_EXPR})"
        )
    )

    bind.execute(sa.text("ALTER TABLE template_permissions ENABLE ROW LEVEL SECURITY"))
    bind.execute(sa.text("ALTER TABLE template_permissions FORCE ROW LEVEL SECURITY"))
    bind.execute(
        sa.text(
            "CREATE POLICY tenant_isolation ON template_permissions "
            "USING (EXISTS ("
            "  SELECT 1 FROM permission_templates pt "
            "  WHERE pt.id = template_permissions.template_id "
            f"  AND (pt.is_system OR pt.tenant_id = {_TENANT_ID_EXPR})"
            ")) "
            "WITH CHECK (EXISTS ("
            "  SELECT 1 FROM permission_templates pt "
            "  WHERE pt.id = template_permissions.template_id "
            f"  AND NOT pt.is_system AND pt.tenant_id = {_TENANT_ID_EXPR}"
            "))"
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    bind.execute(sa.text("DROP POLICY IF EXISTS tenant_isolation ON template_permissions"))
    bind.execute(sa.text("ALTER TABLE template_permissions NO FORCE ROW LEVEL SECURITY"))
    bind.execute(sa.text("ALTER TABLE template_permissions DISABLE ROW LEVEL SECURITY"))

    bind.execute(sa.text("DROP POLICY IF EXISTS tenant_isolation ON permission_templates"))
    bind.execute(sa.text("ALTER TABLE permission_templates NO FORCE ROW LEVEL SECURITY"))
    bind.execute(sa.text("ALTER TABLE permission_templates DISABLE ROW LEVEL SECURITY"))
