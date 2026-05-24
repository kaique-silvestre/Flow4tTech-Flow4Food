"""Fix is_system flag for seed profiles (Admin, Gerente, Caixa)

Revision ID: 0038
Revises: 0037
Create Date: 2026-05-19

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0038"
down_revision: Union[str, None] = "0037"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SYSTEM_PROFILE_NAMES = ("Admin", "Gerente", "Caixa")


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE profiles SET is_system = TRUE "
            "WHERE name IN :names"
        ),
        {"names": SYSTEM_PROFILE_NAMES},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE profiles SET is_system = FALSE "
            "WHERE name IN :names"
        ),
        {"names": SYSTEM_PROFILE_NAMES},
    )
