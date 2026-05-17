"""add numero_dia to comandas

Revision ID: 0034
Revises: 0033
Create Date: 2026-05-15

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0034"
down_revision: Union[str, None] = "0033"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("comandas", sa.Column("numero_dia", sa.Integer(), nullable=True))

    conn = op.get_bind()
    # Backfill: rank existing comandas by created_at within each day
    rows = conn.execute(
        sa.text(
            "SELECT id, DATE(created_at) as dia, created_at "
            "FROM comandas ORDER BY created_at ASC"
        )
    ).fetchall()

    counter: dict = {}
    for row in rows:
        dia = str(row[1])
        counter[dia] = counter.get(dia, 0) + 1
        conn.execute(
            sa.text("UPDATE comandas SET numero_dia = :n WHERE id = :id"),
            {"n": counter[dia], "id": row[0]},
        )


def downgrade() -> None:
    op.drop_column("comandas", "numero_dia")
