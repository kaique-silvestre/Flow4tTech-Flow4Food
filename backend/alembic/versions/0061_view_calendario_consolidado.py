"""view_calendario_consolidado: UNION ALL 4 camadas por tenant

Revision ID: 0061
Revises: 0060
"""

from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0061"
down_revision: Union[str, None] = "0060"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        conn.execute(sa.text("""
            CREATE OR REPLACE VIEW view_calendario_consolidado AS
            SELECT
                tenant_id,
                data_evento AS data_referencia,
                'evento'::text AS tipo,
                id AS referencia_id,
                titulo AS descricao,
                NULL::TIME AS hora_inicio,
                NULL::NUMERIC AS valor,
                NULL::TEXT AS fornecedor_nome
            FROM tenant_eventos
            UNION ALL
            SELECT
                tenant_id,
                data_inicio AS data_referencia,
                'promocao'::text AS tipo,
                id AS referencia_id,
                nome AS descricao,
                hora_inicio,
                NULL::NUMERIC AS valor,
                NULL::TEXT AS fornecedor_nome
            FROM promocoes
            WHERE data_fim IS NULL OR data_fim >= CURRENT_DATE
            UNION ALL
            SELECT
                cp.tenant_id,
                cp.data_vencimento AS data_referencia,
                'conta_pagar'::text AS tipo,
                cp.id AS referencia_id,
                COALESCE(f.nome, 'Sem fornecedor') AS descricao,
                NULL::TIME AS hora_inicio,
                cp.valor,
                f.nome AS fornecedor_nome
            FROM contas_pagar cp
            LEFT JOIN fornecedores f ON f.id = cp.fornecedor_id
            WHERE cp.status = 'pendente'
            UNION ALL
            SELECT
                c.tenant_id,
                c.data_prevista_recebimento AS data_referencia,
                'entrega_insumo'::text AS tipo,
                c.id AS referencia_id,
                COALESCE(f.nome, 'Sem fornecedor') AS descricao,
                '08:00:00'::TIME AS hora_inicio,
                NULL::NUMERIC AS valor,
                f.nome AS fornecedor_nome
            FROM compras c
            LEFT JOIN fornecedores f ON f.id = c.fornecedor_id
            WHERE c.status = 'confirmado' AND c.data_prevista_recebimento IS NOT NULL
        """))


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        conn.execute(sa.text("DROP VIEW IF EXISTS view_calendario_consolidado"))
