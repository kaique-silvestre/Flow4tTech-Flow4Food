"""create tenants table

Revision ID: 0042
Revises: 0041
Create Date: 2026-05-28

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0042"
down_revision: Union[str, None] = "0041"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("nome_fantasia", sa.String(200), nullable=False),
        sa.Column("cnpj", sa.String(18), nullable=True, unique=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ativo"),
        sa.Column("admin_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_tenants_status", "tenants", ["status"])

    # Seed default tenant so existing server_default="1" FKs remain valid
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        bind.execute(
            sa.text(
                "INSERT INTO tenants (id, nome_fantasia, status) VALUES (1, 'Tenant Padrão', 'ativo') "
                "ON CONFLICT (id) DO NOTHING"
            )
        )
    else:
        bind.execute(
            sa.text(
                "INSERT OR IGNORE INTO tenants (id, nome_fantasia, status) VALUES (1, 'Tenant Padrão', 'ativo')"
            )
        )


def downgrade() -> None:
    op.drop_index("ix_tenants_status", "tenants")
    op.drop_table("tenants")
