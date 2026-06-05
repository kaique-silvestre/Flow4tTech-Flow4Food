"""grant USAGE on existing sequences to app_user

Revision ID: 0051
Revises: 0050
Create Date: 2026-06-03

Migration 0050 set ALTER DEFAULT PRIVILEGES so *future* sequences are granted
to app_user, but the sequences that already existed (e.g. categorias_id_seq)
were never granted. Inserts via SET LOCAL ROLE app_user therefore failed with
"permission denied for sequence ...". This grants USAGE, SELECT on all current
sequences in the public schema.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0051"
down_revision: Union[str, None] = "0050"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _role_exists(bind, role_name: str) -> bool:
    row = bind.execute(
        sa.text("SELECT 1 FROM pg_roles WHERE rolname = :r"),
        {"r": role_name},
    ).fetchone()
    return row is not None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    if not _role_exists(bind, "app_user"):
        return
    bind.execute(sa.text("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user"))


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    bind.execute(sa.text("REVOKE USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public FROM app_user"))
