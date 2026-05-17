"""Seed usuário Admin inicial

Revision ID: 0036
Revises: 0035
Create Date: 2026-05-17

"""

from typing import Sequence, Union

import bcrypt
from alembic import op
import sqlalchemy as sa

revision: str = "0036"
down_revision: Union[str, None] = "0035"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TENANT_ID = 1
DEFAULT_PASSWORD = "admin123"


def _hash(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def upgrade() -> None:
    conn = op.get_bind()

    admin_profile = conn.execute(
        sa.text("SELECT id FROM profiles WHERE tenant_id = :tid AND name = 'Admin'"),
        {"tid": TENANT_ID},
    ).fetchone()

    if admin_profile is None:
        return

    existing = conn.execute(
        sa.text("SELECT id FROM system_users WHERE tenant_id = :tid AND username = 'admin'"),
        {"tid": TENANT_ID},
    ).fetchone()

    if existing is None:
        conn.execute(
            sa.text(
                "INSERT INTO system_users (tenant_id, profile_id, name, username, email, password_hash, is_active) "
                "VALUES (:tid, :pid, :name, :username, :email, :phash, true)"
            ),
            {
                "tid": TENANT_ID,
                "pid": admin_profile[0],
                "name": "Administrador",
                "username": "admin",
                "email": None,
                "phash": _hash(DEFAULT_PASSWORD),
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM system_users WHERE tenant_id = :tid AND username = 'admin'"),
        {"tid": TENANT_ID},
    )
