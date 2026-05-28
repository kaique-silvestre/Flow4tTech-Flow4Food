"""add tenant_id to operational tables and enable RLS

Revision ID: 0043
Revises: 0042
Create Date: 2026-05-28

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0043"
down_revision: Union[str, None] = "0042"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables that get a new tenant_id column (profiles/system_users already have it)
_NEW_TENANT_TABLES = [
    "categorias",
    "fornecedores",
    "insumos",
    "produtos",
    "movimentos_estoque",
    "compras",
    "comandas",
    "itens_comanda",
    "pagamentos",
    "comissoes_garcom",
    "eventos_comanda",
    "profile_permissions",
]

# All tables that need RLS (includes profiles/system_users which already have tenant_id)
_RLS_TABLES = _NEW_TENANT_TABLES + ["profiles", "system_users"]

# Composite indexes: (tenant_id, secondary_col) for high-read tables
_COMPOSITE_INDEXES = {
    "categorias": ["nome"],
    "fornecedores": ["nome"],
    "insumos": ["nome"],
    "produtos": ["nome"],
    "comandas": ["status", "created_at"],
    "pagamentos": ["comanda_id"],
    "movimentos_estoque": ["insumo_id"],
    "system_users": ["username"],
    "profiles": ["name"],
}


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # 1. Add tenant_id to tables that don't have it yet
    for table in _NEW_TENANT_TABLES:
        op.add_column(
            table,
            sa.Column(
                "tenant_id",
                sa.BigInteger(),
                sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
                nullable=False,
                server_default="1",
            ),
        )
        op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id"])

    # 2. Add FK on profiles.tenant_id and system_users.tenant_id (column already exists)
    if is_pg:
        op.create_foreign_key(
            "fk_profiles_tenant_id",
            "profiles",
            "tenants",
            ["tenant_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        op.create_foreign_key(
            "fk_system_users_tenant_id",
            "system_users",
            "tenants",
            ["tenant_id"],
            ["id"],
            ondelete="RESTRICT",
        )

    # 3. Composite indexes (tenant_id, secondary_col) and (tenant_id, id)
    for table, cols in _COMPOSITE_INDEXES.items():
        op.create_index(f"ix_{table}_tenant_id_id", table, ["tenant_id", "id"])
        for col in cols:
            op.create_index(f"ix_{table}_tenant_{col}", table, ["tenant_id", col])

    # 4. PostgreSQL-only: enable RLS and create tenant isolation policies
    if is_pg:
        for table in _RLS_TABLES:
            bind.execute(sa.text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
            bind.execute(
                sa.text(
                    f"CREATE POLICY tenant_isolation ON {table} "
                    f"USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::bigint)"
                )
            )


def downgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # Drop RLS policies first (PostgreSQL only)
    if is_pg:
        for table in _RLS_TABLES:
            bind.execute(sa.text(f"DROP POLICY IF EXISTS tenant_isolation ON {table}"))
            bind.execute(sa.text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY"))

    # Drop composite indexes
    for table, cols in _COMPOSITE_INDEXES.items():
        op.drop_index(f"ix_{table}_tenant_id_id", table)
        for col in cols:
            op.drop_index(f"ix_{table}_tenant_{col}", table)

    # Drop FK constraints on profiles/system_users (PostgreSQL only, column stays)
    if is_pg:
        op.drop_constraint("fk_profiles_tenant_id", "profiles", type_="foreignkey")
        op.drop_constraint("fk_system_users_tenant_id", "system_users", type_="foreignkey")

    # Drop tenant_id columns from new tables
    for table in _NEW_TENANT_TABLES:
        op.drop_index(f"ix_{table}_tenant_id", table)
        op.drop_column(table, "tenant_id")
