"""merge estabelecimento into tenants, add max_users, add is_owner to system_users

Revision ID: 0069
Revises: 0068
Create Date: 2026-06-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0069"
down_revision: Union[str, None] = "0068"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Add new columns to tenants
    op.add_column("tenants", sa.Column("endereco", sa.String(300), nullable=True))
    op.add_column("tenants", sa.Column("telefone", sa.String(30), nullable=True))
    op.add_column(
        "tenants",
        sa.Column("max_users", sa.Integer(), nullable=False, server_default="5"),
    )

    # 2. Add is_owner to system_users
    op.add_column(
        "system_users",
        sa.Column("is_owner", sa.Boolean(), nullable=False, server_default="false"),
    )

    # 3. Copy endereco/telefone from estabelecimento into tenants (if table exists)
    tables = conn.execute(
        sa.text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename='estabelecimento'")
    ).fetchall()
    if tables:
        conn.execute(
            sa.text("""
                UPDATE tenants t
                SET endereco = e.endereco,
                    telefone = e.telefone
                FROM estabelecimento e
                WHERE e.tenant_id = t.id
            """)
        )

    # 4. Mark owner users
    conn.execute(
        sa.text("""
            UPDATE system_users su
            SET is_owner = TRUE
            FROM tenants t
            WHERE su.id = t.admin_user_id
        """)
    )

    # 5. Drop estabelecimento (if exists)
    if tables:
        op.drop_table("estabelecimento")

    # 6. Grant app_user SELECT on tenants (already has it, but enforce)
    # UPDATE on tenants is intentionally NOT granted to app_user —
    # config updates use superuser connection with explicit tenant_id validation.


def downgrade() -> None:
    op.create_table(
        "estabelecimento",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("nome", sa.String(200), nullable=False, server_default="Estabelecimento"),
        sa.Column("cnpj", sa.String(20), nullable=True),
        sa.Column("endereco", sa.String(300), nullable=True),
        sa.Column("telefone", sa.String(30), nullable=True),
    )
    op.drop_column("tenants", "endereco")
    op.drop_column("tenants", "telefone")
    op.drop_column("tenants", "max_users")
    op.drop_column("system_users", "is_owner")
