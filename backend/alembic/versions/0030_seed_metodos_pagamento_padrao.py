"""seed metodos pagamento padrao

Revision ID: 0030
Revises: 0029
Create Date: 2026-05-14

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0030"
down_revision: Union[str, None] = "0029_estoque_reservado"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PADROES = [
    ("Dinheiro", "dinheiro"),
    ("PIX", "pix"),
    ("Débito", "debito"),
    ("Crédito", "credito"),
]


def upgrade() -> None:
    conn = op.get_bind()
    for nome, tipo in PADROES:
        exists = conn.execute(
            sa.text("SELECT 1 FROM metodos_pagamento WHERE nome = :nome"),
            {"nome": nome},
        ).fetchone()
        if not exists:
            conn.execute(
                sa.text(
                    "INSERT INTO metodos_pagamento (nome, ativo, tipo) VALUES (:nome, true, :tipo)"
                ),
                {"nome": nome, "tipo": tipo},
            )


def downgrade() -> None:
    conn = op.get_bind()
    for nome, _ in PADROES:
        conn.execute(
            sa.text("DELETE FROM metodos_pagamento WHERE nome = :nome"),
            {"nome": nome},
        )
