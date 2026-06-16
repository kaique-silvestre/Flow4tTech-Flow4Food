"""fix promocoes.tipo_desconto length — VARCHAR(10) too short for 'porcentagem'

Revision ID: 0066
Revises: 0065
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0066"
down_revision: Union[str, None] = "0065"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return
    conn.execute(sa.text(
        "ALTER TABLE promocoes ALTER COLUMN tipo_desconto TYPE VARCHAR(20)"
    ))


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return
    conn.execute(sa.text(
        "ALTER TABLE promocoes ALTER COLUMN tipo_desconto TYPE VARCHAR(10)"
    ))
