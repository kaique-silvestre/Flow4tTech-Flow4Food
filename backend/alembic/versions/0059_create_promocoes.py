"""promocoes: schema + RLS + ENUM tipo_recorrencia

Revision ID: 0059
Revises: 0058
"""

from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0059"
down_revision: Union[str, None] = "0058"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    is_pg = conn.dialect.name == "postgresql"

    dias_type = sa.ARRAY(sa.Integer()) if is_pg else sa.JSON()

    op.create_table(
        "promocoes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column(
            "tipo_desconto",
            sa.String(10),
            sa.CheckConstraint("tipo_desconto IN ('porcentagem', 'valor_fixo')", name="chk_tipo_desconto"),
            nullable=False,
        ),
        sa.Column("valor_desconto", sa.Numeric(10, 2), nullable=False),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("data_fim", sa.Date(), nullable=True),
        sa.Column("hora_inicio", sa.Time(), nullable=False, server_default="00:00:00"),
        sa.Column("hora_fim", sa.Time(), nullable=False, server_default="23:59:59"),
        sa.Column("recorrencia", sa.String(10), nullable=False, server_default="nenhuma"),
        sa.Column("dias_semana", dias_type, nullable=True),
        sa.Column("dias_mes", dias_type, nullable=True),
        sa.Column(
            "criado_por",
            sa.BigInteger(),
            sa.ForeignKey("system_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "promocao_produtos",
        sa.Column("promocao_id", sa.BigInteger(), sa.ForeignKey("promocoes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("produto_id", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("promocao_id", "produto_id"),
    )

    op.create_index(
        "idx_promocoes_vigencia",
        "promocoes",
        ["tenant_id", "data_inicio", "data_fim"],
    )

    if is_pg:
        conn.execute(sa.text(
            "DO $$ BEGIN "
            "CREATE TYPE tipo_recorrencia AS ENUM ('nenhuma', 'semanal', 'mensal'); "
            "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
        ))
        conn.execute(sa.text(
            "ALTER TABLE promocoes ALTER COLUMN recorrencia DROP DEFAULT"
        ))
        conn.execute(sa.text(
            "ALTER TABLE promocoes "
            "ALTER COLUMN recorrencia TYPE tipo_recorrencia "
            "USING recorrencia::tipo_recorrencia"
        ))
        conn.execute(sa.text(
            "ALTER TABLE promocoes ALTER COLUMN recorrencia SET DEFAULT 'nenhuma'::tipo_recorrencia"
        ))
        conn.execute(sa.text("ALTER TABLE promocoes ENABLE ROW LEVEL SECURITY"))
        conn.execute(sa.text(
            "CREATE POLICY tenant_isolation ON promocoes "
            "USING (tenant_id = (NULLIF(current_setting('app.tenant_id', true), ''))::bigint)"
        ))
        conn.execute(sa.text(
            "INSERT INTO template_permissions (template_id, screen, can_access) "
            "SELECT pt.id, 'promocoes', true "
            "FROM permission_templates pt "
            "WHERE pt.is_system = true AND pt.nome IN ('Admin', 'Gerente') "
            "ON CONFLICT DO NOTHING"
        ))


def downgrade() -> None:
    conn = op.get_bind()
    is_pg = conn.dialect.name == "postgresql"

    if is_pg:
        conn.execute(sa.text("DROP POLICY IF EXISTS tenant_isolation ON promocoes"))
    op.drop_index("idx_promocoes_vigencia", table_name="promocoes")
    op.drop_table("promocao_produtos")
    op.drop_table("promocoes")
    if is_pg:
        conn.execute(sa.text("DROP TYPE IF EXISTS tipo_recorrencia"))
