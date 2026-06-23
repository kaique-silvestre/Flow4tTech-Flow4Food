"""grant SELECT on permission_templates and template_permissions to app_user

Revision ID: 0068
Revises: 0067
Create Date: 2026-06-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0068"
down_revision: Union[str, None] = "0067"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return
    conn.execute(sa.text("GRANT SELECT ON TABLE permission_templates TO app_user"))
    conn.execute(sa.text("GRANT SELECT ON TABLE template_permissions TO app_user"))


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return
    conn.execute(sa.text("REVOKE SELECT ON TABLE permission_templates FROM app_user"))
    conn.execute(sa.text("REVOKE SELECT ON TABLE template_permissions FROM app_user"))
