"""add padrao to metodos_pagamento

Revision ID: 0032
Revises: 0031
Create Date: 2026-05-14

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0032"
down_revision: Union[str, None] = "0031"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PADROES = ["Dinheiro", "PIX", "Débito", "Crédito"]


def upgrade() -> None:
    op.add_column(
        "metodos_pagamento",
        sa.Column("padrao", sa.Boolean(), nullable=False, server_default="false"),
    )
    conn = op.get_bind()
    for nome in PADROES:
        conn.execute(
            sa.text("UPDATE metodos_pagamento SET padrao = true WHERE nome = :nome"),
            {"nome": nome},
        )


def downgrade() -> None:
    op.drop_column("metodos_pagamento", "padrao")
