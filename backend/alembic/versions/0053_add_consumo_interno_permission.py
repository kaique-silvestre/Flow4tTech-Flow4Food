"""add consumo_interno permission to Admin and Gerente profiles

Revision ID: 0053
Revises: 0052
Create Date: 2026-06-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0053"
down_revision: Union[str, None] = "0052"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCREEN = "consumo_interno"
PROFILE_NAMES = ("Admin", "Gerente")

OLD_SCREENS = (
    "dashboard", "comandas", "compras", "estoque",
    "cadastros", "relatorios", "configuracoes", "gestao_usuarios",
)
NEW_SCREENS = OLD_SCREENS + (SCREEN,)


def upgrade() -> None:
    conn = op.get_bind()
    is_pg = conn.dialect.name == "postgresql"

    # Expand CHECK constraint to accept the new screen value
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
            # Set RLS context so FORCE ROW LEVEL SECURITY allows the INSERT
            if is_pg:
                conn.execute(
                    sa.text(f"SET LOCAL app.tenant_id = '{int(tenant_id)}'")
                )
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
                        "INSERT INTO profile_permissions (tenant_id, profile_id, screen, can_access) "
                        "VALUES (:tid, :pid, :screen, true)"
                    ),
                    {"tid": tenant_id, "pid": profile_id, "screen": SCREEN},
                )


def downgrade() -> None:
    conn = op.get_bind()
    is_pg = conn.dialect.name == "postgresql"

    for name in PROFILE_NAMES:
        rows = conn.execute(
            sa.text("SELECT id FROM profiles WHERE name = :name"),
            {"name": name},
        ).fetchall()
        for (profile_id,) in rows:
            conn.execute(
                sa.text(
                    "DELETE FROM profile_permissions "
                    "WHERE profile_id = :pid AND screen = :screen"
                ),
                {"pid": profile_id, "screen": SCREEN},
            )

    # Restore original CHECK constraint without consumo_interno
    if is_pg:
        conn.execute(sa.text(
            "ALTER TABLE profile_permissions DROP CONSTRAINT IF EXISTS ck_permission_screen"
        ))
        conn.execute(sa.text(
            f"ALTER TABLE profile_permissions ADD CONSTRAINT ck_permission_screen "
            f"CHECK (screen IN {OLD_SCREENS!r})"
        ))
