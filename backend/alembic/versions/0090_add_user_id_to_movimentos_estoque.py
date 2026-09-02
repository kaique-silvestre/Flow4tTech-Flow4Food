"""movimentos_estoque: add user_id FK system_users

Auditoria apontou que a baixa manual de estoque ("baixa-sem-venda") nao
tinha vinculo de autor: nenhuma coluna registrava qual usuario autenticado
executou o movimento. Segue o padrao ja usado em tenant_eventos.criado_por
e promocoes.criado_por (FK nullable, ondelete SET NULL — o movimento
historico deve sobreviver a exclusao do usuario).

Revision ID: 0090
Revises: 0089
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0090"
down_revision: Union[str, None] = "0089"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.add_column(
            "movimentos_estoque",
            sa.Column(
                "user_id",
                sa.BigInteger(),
                sa.ForeignKey("system_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.drop_column("movimentos_estoque", "user_id")
