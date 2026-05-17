"""Seed perfis padrão do sistema (Admin, Gerente, Caixa)

Revision ID: 0035
Revises: 0034
Create Date: 2026-05-17

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0035"
down_revision: Union[str, None] = "0034"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TENANT_ID = 1
ALL_SCREENS = [
    "dashboard", "comandas", "compras", "estoque",
    "cadastros", "relatorios", "configuracoes", "gestao_usuarios",
]
GERENTE_SCREENS = [s for s in ALL_SCREENS if s not in ("configuracoes", "gestao_usuarios")]
CAIXA_SCREENS = ["dashboard", "comandas", "estoque"]

PROFILES = [
    {"name": "Admin", "description": "Acesso total ao sistema", "is_system": True, "screens": ALL_SCREENS},
    {"name": "Gerente", "description": "Acesso gerencial (sem configurações)", "is_system": True, "screens": GERENTE_SCREENS},
    {"name": "Caixa", "description": "Acesso operacional básico", "is_system": True, "screens": CAIXA_SCREENS},
]


def upgrade() -> None:
    conn = op.get_bind()

    for profile_data in PROFILES:
        existing = conn.execute(
            sa.text("SELECT id FROM profiles WHERE tenant_id = :tid AND name = :name"),
            {"tid": TENANT_ID, "name": profile_data["name"]},
        ).fetchone()

        if existing:
            profile_id = existing[0]
        else:
            result = conn.execute(
                sa.text(
                    "INSERT INTO profiles (tenant_id, name, description, is_system) "
                    "VALUES (:tid, :name, :desc, :is_system) RETURNING id"
                ),
                {
                    "tid": TENANT_ID,
                    "name": profile_data["name"],
                    "desc": profile_data["description"],
                    "is_system": profile_data["is_system"],
                },
            )
            profile_id = result.fetchone()[0]

        for screen in profile_data["screens"]:
            perm_exists = conn.execute(
                sa.text("SELECT id FROM profile_permissions WHERE profile_id = :pid AND screen = :screen"),
                {"pid": profile_id, "screen": screen},
            ).fetchone()
            if not perm_exists:
                conn.execute(
                    sa.text(
                        "INSERT INTO profile_permissions (profile_id, screen, can_access) "
                        "VALUES (:pid, :screen, true)"
                    ),
                    {"pid": profile_id, "screen": screen},
                )


def downgrade() -> None:
    conn = op.get_bind()
    for profile_data in PROFILES:
        conn.execute(
            sa.text("DELETE FROM profiles WHERE tenant_id = :tid AND name = :name AND is_system = true"),
            {"tid": TENANT_ID, "name": profile_data["name"]},
        )
