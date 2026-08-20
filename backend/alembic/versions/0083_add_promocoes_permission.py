"""add promocoes permission screen to constraint and Admin/Gerente profiles

Revision ID: 0083
Revises: 0082
Create Date: 2026-08-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0083"
down_revision: Union[str, None] = "0082"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCREEN = "promocoes"
PROFILE_NAMES = ("Admin", "Gerente")

OLD_SCREENS = (
    "dashboard", "comandas", "compras", "estoque",
    "cadastros", "relatorios", "configuracoes", "gestao_usuarios",
    "consumo_interno", "calendario", "financeiro",
)
NEW_SCREENS = OLD_SCREENS + (SCREEN,)


def upgrade() -> None:
    conn = op.get_bind()
    is_pg = conn.dialect.name == "postgresql"

    if is_pg:
        conn.execute(sa.text(
            "ALTER TABLE profile_permissions DROP CONSTRAINT IF EXISTS ck_permission_screen"
        ))
        conn.execute(sa.text(
            f"ALTER TABLE profile_permissions ADD CONSTRAINT ck_permission_screen "
            f"CHECK (screen IN {NEW_SCREENS!r})"
        ))

    for name in PROFILE_NAMES:
        rows = conn.execute(
            sa.text("SELECT id, tenant_id FROM profiles WHERE name = :name"),
            {"name": name},
        ).fetchall()
        for profile_id, tenant_id in rows:
            if is_pg:
                conn.execute(sa.text(f"SET LOCAL app.tenant_id = '{int(tenant_id)}'"))
            exists = conn.execute(
                sa.text(
                    "SELECT id FROM profile_permissions "
                    "WHERE profile_id = :pid AND screen = :screen"
                ),
                {"pid": profile_id, "screen": SCREEN},
            ).fetchone()
            if not exists:
                conn.execute(
                    sa.text(
                        "INSERT INTO profile_permissions (profile_id, tenant_id, screen) "
                        "VALUES (:pid, :tid, :screen)"
                    ),
                    {"pid": profile_id, "tid": tenant_id, "screen": SCREEN},
                )

    # also patch template_permissions (profiles linked to a template bypass profile_permissions)
    template_rows = conn.execute(
        sa.text(
            "SELECT DISTINCT p.template_id FROM profiles p "
            "WHERE p.name IN ('Admin', 'Gerente') AND p.template_id IS NOT NULL"
        )
    ).fetchall()
    for (template_id,) in template_rows:
        exists = conn.execute(
            sa.text("SELECT template_id FROM template_permissions WHERE template_id = :tid AND screen = :screen"),
            {"tid": template_id, "screen": SCREEN},
        ).fetchone()
        if not exists:
            conn.execute(
                sa.text(
                    "INSERT INTO template_permissions (template_id, screen, can_access) "
                    "VALUES (:tid, :screen, true)"
                ),
                {"tid": template_id, "screen": SCREEN},
            )


def downgrade() -> None:
    conn = op.get_bind()
    is_pg = conn.dialect.name == "postgresql"

    rows = conn.execute(
        sa.text("SELECT id, tenant_id FROM profiles WHERE name IN ('Admin', 'Gerente')")
    ).fetchall()
    for profile_id, tenant_id in rows:
        if is_pg:
            conn.execute(sa.text(f"SET LOCAL app.tenant_id = '{int(tenant_id)}'"))
        conn.execute(
            sa.text("DELETE FROM profile_permissions WHERE profile_id = :pid AND screen = :screen"),
            {"pid": profile_id, "screen": SCREEN},
        )

    if is_pg:
        conn.execute(sa.text(
            "ALTER TABLE profile_permissions DROP CONSTRAINT IF EXISTS ck_permission_screen"
        ))
        conn.execute(sa.text(
            f"ALTER TABLE profile_permissions ADD CONSTRAINT ck_permission_screen "
            f"CHECK (screen IN {OLD_SCREENS!r})"
        ))
