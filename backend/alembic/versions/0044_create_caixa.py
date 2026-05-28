"""create caixa_sessoes and caixa_movimentos

Revision ID: 0044
Revises: 0043
Create Date: 2026-05-28

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0044"
down_revision: Union[str, None] = "0043"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RLS_POLICY = (
    "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::bigint)"
)


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    op.create_table(
        "caixa_sessoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(), nullable=False, server_default="aberta"),
        sa.Column("valor_abertura", sa.Numeric(10, 2), nullable=False),
        sa.Column("valor_informado", sa.Numeric(10, 2), nullable=True),
        sa.Column("valor_esperado", sa.Numeric(10, 2), nullable=True),
        sa.Column("diferenca", sa.Numeric(10, 2), nullable=True),
        sa.Column("aberto_por_user_id", sa.Integer(), nullable=False),
        sa.Column("fechado_por_user_id", sa.Integer(), nullable=True),
        sa.Column("opened_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "caixa_movimentos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("sessao_id", sa.Integer(), sa.ForeignKey("caixa_sessoes.id"), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_caixa_sessoes_tenant_id", "caixa_sessoes", ["tenant_id", "id"])
    op.create_index("ix_caixa_movimentos_sessao", "caixa_movimentos", ["tenant_id", "sessao_id"])

    if is_pg:
        # Partial unique index: at most one open session per tenant
        op.execute(
            "CREATE UNIQUE INDEX uq_caixa_sessoes_tenant_aberta "
            "ON caixa_sessoes (tenant_id) WHERE status = 'aberta'"
        )

        for table in ("caixa_sessoes", "caixa_movimentos"):
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
            op.execute(
                f"CREATE POLICY tenant_isolation ON {table} "
                f"USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::bigint)"
            )


def downgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    if is_pg:
        for table in ("caixa_movimentos", "caixa_sessoes"):
            op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
            op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
        op.execute("DROP INDEX IF EXISTS uq_caixa_sessoes_tenant_aberta")

    op.drop_index("ix_caixa_movimentos_sessao", table_name="caixa_movimentos")
    op.drop_index("ix_caixa_sessoes_tenant_id", table_name="caixa_sessoes")
    op.drop_table("caixa_movimentos")
    op.drop_table("caixa_sessoes")
