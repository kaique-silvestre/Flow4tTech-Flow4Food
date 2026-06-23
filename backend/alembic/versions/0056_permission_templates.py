"""permission templates: tabelas + seed dos perfis de sistema

Cria permission_templates, template_permissions e profiles.template_id.
Seed: para cada perfil is_system existente cria um template de sistema
(tenant_id NULL) espelhando suas telas e vincula via profiles.template_id.

Revision ID: 0056
Revises: 0055
"""

from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0056"
down_revision: Union[str, None] = "0055"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "permission_templates",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=True),
        sa.Column("nome", sa.String(60), nullable=False),
        sa.Column("descricao", sa.String(200), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_table(
        "template_permissions",
        sa.Column("template_id", sa.BigInteger(), nullable=False),
        sa.Column("screen", sa.String(50), nullable=False),
        sa.Column("can_access", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["template_id"], ["permission_templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("template_id", "screen"),
    )
    op.add_column(
        "profiles",
        sa.Column("template_id", sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        "fk_profiles_template_id",
        "profiles",
        "permission_templates",
        ["template_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Seed: espelhar perfis is_system existentes como templates de sistema.
    conn = op.get_bind()
    sys_profiles = conn.execute(
        sa.text(
            "SELECT id, name, description FROM profiles WHERE is_system = true ORDER BY id"
        )
    ).fetchall()

    for prof_id, name, description in sys_profiles:
        result = conn.execute(
            sa.text(
                "INSERT INTO permission_templates (tenant_id, nome, descricao, is_system) "
                "VALUES (NULL, :nome, :desc, true) RETURNING id"
            ),
            {"nome": name, "desc": description},
        )
        template_id = result.fetchone()[0]

        screens = conn.execute(
            sa.text(
                "SELECT screen, can_access FROM profile_permissions WHERE profile_id = :pid"
            ),
            {"pid": prof_id},
        ).fetchall()
        for screen, can_access in screens:
            conn.execute(
                sa.text(
                    "INSERT INTO template_permissions (template_id, screen, can_access) "
                    "VALUES (:tid, :screen, :can)"
                ),
                {"tid": template_id, "screen": screen, "can": can_access},
            )

        conn.execute(
            sa.text("UPDATE profiles SET template_id = :tid WHERE id = :pid"),
            {"tid": template_id, "pid": prof_id},
        )


def downgrade() -> None:
    op.drop_constraint("fk_profiles_template_id", "profiles", type_="foreignkey")
    op.drop_column("profiles", "template_id")
    op.drop_table("template_permissions")
    op.drop_table("permission_templates")
