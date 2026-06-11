"""tenant_eventos: calendário de eventos por tenant com RLS

Revision ID: 0058
Revises: 0057
"""

from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0058"
down_revision: Union[str, None] = "0057"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_eventos",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("titulo", sa.String(100), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("data_evento", sa.Date(), nullable=False),
        sa.Column(
            "criado_por",
            sa.BigInteger(),
            sa.ForeignKey("system_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index(
        "idx_tenant_eventos_data",
        "tenant_eventos",
        ["tenant_id", "data_evento"],
    )

    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        conn.execute(sa.text("ALTER TABLE tenant_eventos ENABLE ROW LEVEL SECURITY"))
        conn.execute(sa.text(
            "CREATE POLICY tenant_isolation ON tenant_eventos "
            "USING (tenant_id = (NULLIF(current_setting('app.tenant_id', true), ''))::bigint)"
        ))
        # Seed "calendario" screen for Admin and Gerente system templates
        conn.execute(sa.text(
            "INSERT INTO template_permissions (template_id, screen, can_access) "
            "SELECT pt.id, 'calendario', true "
            "FROM permission_templates pt "
            "WHERE pt.is_system = true AND pt.nome IN ('Admin', 'Gerente') "
            "ON CONFLICT DO NOTHING"
        ))


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        conn.execute(sa.text("DROP POLICY IF EXISTS tenant_isolation ON tenant_eventos"))
    op.drop_index("idx_tenant_eventos_data", table_name="tenant_eventos")
    op.drop_table("tenant_eventos")
