"""create app_user role and grant table permissions for RLS enforcement

Revision ID: 0050
Revises: 0049
Create Date: 2026-06-03

The application calls SET LOCAL ROLE app_user in every authenticated
request (dependencies.py:44) to enforce RLS policies. Without this role
existing, any fresh database will fail on every authenticated endpoint.

This migration:
  1. Creates the app_user role (idempotent — skips if already exists)
  2. Grants USAGE on schema public
  3. Grants SELECT, INSERT, UPDATE, DELETE on all RLS-protected tables
  4. Grants SELECT on shared lookup tables (tenants, assinaturas,
     revoked_tokens, refresh_tokens)
  5. Sets ALTER DEFAULT PRIVILEGES so future tables also get granted
  6. Does NOT grant BYPASSRLS — that is the whole point of this role
  Note: no CONNECT grant needed — app_user is used via SET LOCAL ROLE,
  never opens its own connections.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0050"
down_revision: Union[str, None] = "0049"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables where app_user needs full DML (RLS enforces tenant isolation)
_RLS_TABLES = [
    # from 0043
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
    # from 0044
    "caixa_sessoes",
    "caixa_movimentos",
    # from 0047
    "garcons",
    "metodos_pagamento",
    "contas_pagar",
    "notificacoes",
    "estabelecimento",
    "ficha_tecnica",
    "itens_compra",
]

# Tables without RLS that authenticated routes may read
_READONLY_TABLES = [
    "tenants",
    "assinaturas",
    "revoked_tokens",
    "refresh_tokens",
]


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    # 1. Create role (idempotent)
    bind.execute(sa.text(
        "DO $$ BEGIN "
        "  CREATE ROLE app_user NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT; "
        "EXCEPTION WHEN duplicate_object THEN NULL; "
        "END $$"
    ))

    # 2. Grant schema usage
    bind.execute(sa.text("GRANT USAGE ON SCHEMA public TO app_user"))

    # 3. Full DML on RLS-protected tables
    for table in _RLS_TABLES:
        bind.execute(sa.text(
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {table} TO app_user"
        ))

    # 4. Read-only on shared lookup tables
    for table in _READONLY_TABLES:
        bind.execute(sa.text(
            f"GRANT SELECT ON TABLE {table} TO app_user"
        ))

    # 5. Default privileges: future tables created by current DB user
    #    also get granted to app_user automatically
    bind.execute(sa.text(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user"
    ))
    bind.execute(sa.text(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT USAGE, SELECT ON SEQUENCES TO app_user"
    ))


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    # Revoke default privileges first
    bind.execute(sa.text(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM app_user"
    ))
    bind.execute(sa.text(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "REVOKE USAGE, SELECT ON SEQUENCES FROM app_user"
    ))

    for table in _READONLY_TABLES:
        bind.execute(sa.text(f"REVOKE ALL ON TABLE {table} FROM app_user"))

    for table in _RLS_TABLES:
        bind.execute(sa.text(f"REVOKE ALL ON TABLE {table} FROM app_user"))

    bind.execute(sa.text("REVOKE USAGE ON SCHEMA public FROM app_user"))
    bind.execute(sa.text("DROP ROLE IF EXISTS app_user"))
