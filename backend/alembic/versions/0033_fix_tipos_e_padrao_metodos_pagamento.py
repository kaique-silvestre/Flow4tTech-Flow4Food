"""fix tipos e padrao dos metodos de pagamento padrao

Revision ID: 0033
Revises: 0032
Create Date: 2026-05-15

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0033"
down_revision: Union[str, None] = "0032"
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
        # Garante que o registro existe
        exists = conn.execute(
            sa.text("SELECT 1 FROM metodos_pagamento WHERE nome = :nome"),
            {"nome": nome},
        ).fetchone()
        if not exists:
            conn.execute(
                sa.text(
                    "INSERT INTO metodos_pagamento (nome, ativo, tipo, padrao) "
                    "VALUES (:nome, true, :tipo, true)"
                ),
                {"nome": nome, "tipo": tipo},
            )
        else:
            conn.execute(
                sa.text(
                    "UPDATE metodos_pagamento SET tipo = :tipo, padrao = true "
                    "WHERE nome = :nome"
                ),
                {"nome": nome, "tipo": tipo},
            )


def downgrade() -> None:
    pass
