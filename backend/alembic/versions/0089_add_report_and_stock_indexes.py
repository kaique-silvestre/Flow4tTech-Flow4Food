"""add indexes for relatorios/dashboard/estoque filter columns

Auditoria apontou table scans em filtros de periodo/agregacao usados por
relatorios financeiros, dashboard, stats de comissao de garcom e consultas
de estoque/compras. Segue a convencao de indices compostos
(tenant_id, coluna) ja usada nas tabelas com RLS (ex.: 0043, 0047, 0082,
0084).

Revision ID: 0089
Revises: 0088
"""

from typing import Union

from alembic import op

revision: str = "0089"
down_revision: Union[str, None] = "0088"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_comandas_tenant_data_fechamento", "comandas", ["tenant_id", "data_fechamento"])
    # ix_comandas_tenant_status já existe (criado em 0043_add_tenant_id_rls) — recriá-lo aqui quebra
    # `alembic upgrade head` num banco novo (DuplicateTable).
    op.create_index("ix_comandas_tenant_garcom_id", "comandas", ["tenant_id", "garcom_id"])

    # ix_pagamentos_tenant_comanda_id já existe (criado em 0043_add_tenant_id_rls).
    op.create_index("ix_pagamentos_tenant_created_at", "pagamentos", ["tenant_id", "created_at"])

    op.create_index("ix_movimentos_estoque_tenant_tipo", "movimentos_estoque", ["tenant_id", "tipo"])
    op.create_index("ix_movimentos_estoque_tenant_created_at", "movimentos_estoque", ["tenant_id", "created_at"])
    # ix_movimentos_estoque_tenant_insumo_id já existe (criado em 0043_add_tenant_id_rls).

    op.create_index("ix_insumos_tenant_categoria_id", "insumos", ["tenant_id", "categoria_id"])
    op.create_index("ix_insumos_tenant_ean", "insumos", ["tenant_id", "ean"])

    op.create_index("ix_compras_tenant_fornecedor_id", "compras", ["tenant_id", "fornecedor_id"])
    op.create_index("ix_compras_tenant_status", "compras", ["tenant_id", "status"])
    op.create_index("ix_compras_tenant_data_compra", "compras", ["tenant_id", "data_compra"])
    op.create_index("ix_compras_tenant_numero_nota", "compras", ["tenant_id", "numero_nota"])

    op.create_index("ix_itens_compra_tenant_compra_id", "itens_compra", ["tenant_id", "compra_id"])
    op.create_index("ix_itens_compra_tenant_insumo_id", "itens_compra", ["tenant_id", "insumo_id"])


def downgrade() -> None:
    op.drop_index("ix_itens_compra_tenant_insumo_id", table_name="itens_compra")
    op.drop_index("ix_itens_compra_tenant_compra_id", table_name="itens_compra")

    op.drop_index("ix_compras_tenant_numero_nota", table_name="compras")
    op.drop_index("ix_compras_tenant_data_compra", table_name="compras")
    op.drop_index("ix_compras_tenant_status", table_name="compras")
    op.drop_index("ix_compras_tenant_fornecedor_id", table_name="compras")

    op.drop_index("ix_insumos_tenant_ean", table_name="insumos")
    op.drop_index("ix_insumos_tenant_categoria_id", table_name="insumos")

    op.drop_index("ix_movimentos_estoque_tenant_created_at", table_name="movimentos_estoque")
    op.drop_index("ix_movimentos_estoque_tenant_tipo", table_name="movimentos_estoque")

    op.drop_index("ix_pagamentos_tenant_created_at", table_name="pagamentos")

    op.drop_index("ix_comandas_tenant_garcom_id", table_name="comandas")
    op.drop_index("ix_comandas_tenant_data_fechamento", table_name="comandas")
