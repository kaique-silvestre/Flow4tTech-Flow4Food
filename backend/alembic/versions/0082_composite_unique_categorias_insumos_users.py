"""fix global unique constraints on categorias.nome, insumos.nome, system_users.email

Revision ID: 0082
Revises: 0081
Create Date: 2026-08-20

categorias.nome (categorias_nome_key, from 0003), insumos.nome
(ix_insumos_nome_unique, from 0021) and system_users.email
(ix_system_users_email, from 0034) were all created with GLOBAL unique
constraints/indexes, which incorrectly prevents two different tenants from
using the same categoria name, insumo name, or user email. This mirrors the
same fix already applied to metodos_pagamento in 0047: drop the global
uniqueness and replace it with a composite UNIQUE(tenant_id, col).

The non-unique composite indexes ix_categorias_tenant_nome and
ix_insumos_tenant_nome (added in 0043 for read performance) become
redundant once the new unique constraints cover the same leading columns,
so they are dropped. system_users has no such composite index on email.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0082"
down_revision: Union[str, None] = "0081"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("categorias_nome_key", "categorias", type_="unique")
    op.create_unique_constraint("uq_categorias_tenant_nome", "categorias", ["tenant_id", "nome"])
    op.drop_index("ix_categorias_tenant_nome", table_name="categorias")

    op.drop_index("ix_insumos_nome_unique", table_name="insumos")
    op.create_unique_constraint("uq_insumos_tenant_nome", "insumos", ["tenant_id", "nome"])
    op.drop_index("ix_insumos_tenant_nome", table_name="insumos")

    op.drop_index("ix_system_users_email", table_name="system_users")
    op.create_unique_constraint("uq_system_users_tenant_email", "system_users", ["tenant_id", "email"])


def downgrade() -> None:
    op.drop_constraint("uq_system_users_tenant_email", "system_users", type_="unique")
    op.create_index("ix_system_users_email", "system_users", ["email"], unique=True)

    op.create_index("ix_insumos_tenant_nome", "insumos", ["tenant_id", "nome"])
    op.drop_constraint("uq_insumos_tenant_nome", "insumos", type_="unique")
    op.create_index("ix_insumos_nome_unique", "insumos", ["nome"], unique=True)

    op.create_index("ix_categorias_tenant_nome", "categorias", ["tenant_id", "nome"])
    op.drop_constraint("uq_categorias_tenant_nome", "categorias", type_="unique")
    op.create_unique_constraint("categorias_nome_key", "categorias", ["nome"])
