"""create itens_consumo_interno and add saida_consumo_interno movement type

Revision ID: 0052
Revises: 0051
Create Date: 2026-06-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0052"
down_revision: Union[str, None] = "0051"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    op.create_table(
        "itens_consumo_interno",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("consumidor_id", sa.Integer(), sa.ForeignKey("system_users.id"), nullable=False),
        sa.Column("produto_id", sa.Integer(), sa.ForeignKey("produtos.id"), nullable=False),
        sa.Column("quantidade", sa.Numeric(10, 4), nullable=False),
        sa.Column("custo_unitario", sa.Numeric(10, 4), nullable=False),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_itens_consumo_interno_tenant",
        "itens_consumo_interno",
        ["tenant_id", "consumidor_id", "created_at"],
    )

    if is_pg:
        op.execute("ALTER TABLE itens_consumo_interno ENABLE ROW LEVEL SECURITY")
        op.execute(
            "CREATE POLICY tenant_isolation ON itens_consumo_interno "
            "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::bigint)"
        )
        # Grant permissions to app_user (if role exists)
        role_exists = bind.execute(
            sa.text("SELECT 1 FROM pg_roles WHERE rolname = 'app_user'")
        ).fetchone()
        if role_exists:
            op.execute(
                "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE itens_consumo_interno TO app_user"
            )
            op.execute(
                "GRANT USAGE, SELECT ON SEQUENCE itens_consumo_interno_id_seq TO app_user"
            )


def downgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    if is_pg:
        op.execute("DROP POLICY IF EXISTS tenant_isolation ON itens_consumo_interno")
        op.execute("ALTER TABLE itens_consumo_interno DISABLE ROW LEVEL SECURITY")

    op.drop_index("ix_itens_consumo_interno_tenant", table_name="itens_consumo_interno")
    op.drop_table("itens_consumo_interno")
