"""force RLS on all tenant-isolated tables and fix INSERT default for tenant_id

Revision ID: 0049
Revises: 0048
Create Date: 2026-06-03

Without FORCE ROW LEVEL SECURITY the table owner (matchpoint) bypasses all
RLS policies, leaking every tenant's rows to every other tenant.
Also changes server_default for tenant_id columns from hardcoded '1' to
current_setting('app.tenant_id') so new rows automatically inherit the
session's tenant without Python code needing to set it explicitly.

Covers all tables with RLS: those from 0043, 0044 (caixa), and 0047 (missing tables).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0049"
down_revision: Union[str, None] = "0048"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RLS_TABLES = [
    # from migration 0043
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
    "profiles",
    "system_users",
    # from migration 0044
    "caixa_sessoes",
    "caixa_movimentos",
    # from migration 0047
    "garcons",
    "metodos_pagamento",
    "contas_pagar",
    "notificacoes",
    "estabelecimento",
    "ficha_tecnica",
    "itens_compra",
]

_TENANT_DEFAULT_EXPR = (
    "(NULLIF(current_setting('app.tenant_id', true), ''))::bigint"
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    for table in _RLS_TABLES:
        bind.execute(sa.text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
        bind.execute(
            sa.text(
                f"ALTER TABLE {table} "
                f"ALTER COLUMN tenant_id SET DEFAULT {_TENANT_DEFAULT_EXPR}"
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    for table in _RLS_TABLES:
        bind.execute(sa.text(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY"))
        bind.execute(
            sa.text(f"ALTER TABLE {table} ALTER COLUMN tenant_id SET DEFAULT 1")
        )
