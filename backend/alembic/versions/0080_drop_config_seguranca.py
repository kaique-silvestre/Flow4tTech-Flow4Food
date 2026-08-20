"""drop config_seguranca table (dead code / global-secret vuln)

Revision ID: 0080
Revises: 0079
Create Date: 2026-08-20

config_seguranca was a single global row (no tenant_id, no RLS) shared
across every tenant on the platform. Its only consumer, the old
single-password login flow, was already retired and returns HTTP 410
(see auth_service.authenticate). The PATCH /api/config/senha endpoint
backed by this table let any user with the "configuracoes" permission
overwrite a "security password" shared by all tenants. Removed as dead
code rather than patched with tenant_id/RLS.

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0080"
down_revision: Union[str, None] = "0079"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("config_seguranca")


def downgrade() -> None:
    op.create_table(
        "config_seguranca",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("senha_hash", sa.String, nullable=False),
    )
