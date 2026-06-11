"""itens_comanda: add promocao_id FK promocoes

Revision ID: 0062
Revises: 0061
"""

from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0062"
down_revision: Union[str, None] = "0061"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.add_column(
            "itens_comanda",
            sa.Column("promocao_id", sa.BigInteger(), sa.ForeignKey("promocoes.id", ondelete="SET NULL"), nullable=True),
        )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.drop_column("itens_comanda", "promocao_id")
