"""add tenant_id and RLS to tables missing isolation

Revision ID: 0047
Revises: 0046
Create Date: 2026-05-29

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0047"
down_revision: Union[str, None] = "0046"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = [
    "garcons",
    "metodos_pagamento",
    "contas_pagar",
    "notificacoes",
    "estabelecimento",
    "ficha_tecnica",
    "itens_compra",
]


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # 1. Add tenant_id to all missing tables (nullable first to populate, then NOT NULL)
    for table in _TABLES:
        op.add_column(
            table,
            sa.Column(
                "tenant_id",
                sa.BigInteger(),
                nullable=True,
            ),
        )

    # 2. Populate tenant_id for existing rows
    bind.execute(sa.text("UPDATE garcons SET tenant_id = 2"))
    bind.execute(sa.text("UPDATE metodos_pagamento SET tenant_id = 2"))
    bind.execute(sa.text("UPDATE contas_pagar SET tenant_id = 2"))
    bind.execute(sa.text("UPDATE notificacoes SET tenant_id = 2"))
    bind.execute(sa.text("UPDATE estabelecimento SET tenant_id = 2"))
    bind.execute(sa.text(
        "UPDATE ficha_tecnica ft SET tenant_id = ("
        "  SELECT tenant_id FROM produtos WHERE produtos.id = ft.produto_id"
        ")"
    ))
    bind.execute(sa.text(
        "UPDATE itens_compra ic SET tenant_id = ("
        "  SELECT tenant_id FROM compras WHERE compras.id = ic.compra_id"
        ")"
    ))

    # 3. Set NOT NULL and default
    for table in _TABLES:
        op.alter_column(table, "tenant_id", nullable=False, server_default="1")
        op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id"])

    # 4. Add FK tenant_id -> tenants.id
    if is_pg:
        for table in _TABLES:
            op.create_foreign_key(
                f"fk_{table}_tenant_id",
                table,
                "tenants",
                ["tenant_id"],
                ["id"],
                ondelete="RESTRICT",
            )

    # 5. Fix metodos_pagamento: drop global unique(nome), add composite unique(tenant_id, nome)
    op.drop_constraint("metodos_pagamento_nome_key", "metodos_pagamento", type_="unique")
    op.create_unique_constraint(
        "uq_metodos_pagamento_tenant_nome",
        "metodos_pagamento",
        ["tenant_id", "nome"],
    )

    # 6. Composite indexes for high-read tables
    op.create_index("ix_garcons_tenant_id_id", "garcons", ["tenant_id", "id"])
    op.create_index("ix_metodos_pagamento_tenant_id_id", "metodos_pagamento", ["tenant_id", "id"])
    op.create_index("ix_ficha_tecnica_tenant_id_id", "ficha_tecnica", ["tenant_id", "id"])
    op.create_index("ix_itens_compra_tenant_id_id", "itens_compra", ["tenant_id", "id"])

    # 7. Enable RLS + tenant isolation policies (PostgreSQL only)
    if is_pg:
        for table in _TABLES:
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

    if is_pg:
        for table in _TABLES:
            bind.execute(sa.text(f"DROP POLICY IF EXISTS tenant_isolation ON {table}"))
            bind.execute(sa.text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY"))

    op.drop_index("ix_garcons_tenant_id_id", "garcons")
    op.drop_index("ix_metodos_pagamento_tenant_id_id", "metodos_pagamento")
    op.drop_index("ix_ficha_tecnica_tenant_id_id", "ficha_tecnica")
    op.drop_index("ix_itens_compra_tenant_id_id", "itens_compra")

    op.drop_constraint("uq_metodos_pagamento_tenant_nome", "metodos_pagamento", type_="unique")
    op.create_unique_constraint("metodos_pagamento_nome_key", "metodos_pagamento", ["nome"])

    if is_pg:
        for table in _TABLES:
            op.drop_constraint(f"fk_{table}_tenant_id", table, type_="foreignkey")

    for table in _TABLES:
        op.drop_index(f"ix_{table}_tenant_id", table)
        op.drop_column(table, "tenant_id")
