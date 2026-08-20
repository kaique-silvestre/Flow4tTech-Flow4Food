"""comandas.total com precisao numerica fixa (10, 2)

Sem escala fixa, um desconto percentual podia deixar total como
66.6666... em vez de 66.67. Alinha com o padrao Numeric(10, 2) usado
em pagamentos.valor, caixa.valor_esperado, etc.

Revision ID: 0087
Revises: 0086
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0087"
down_revision: Union[str, None] = "0086"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "comandas",
        "total",
        existing_type=sa.Numeric(),
        type_=sa.Numeric(10, 2),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "comandas",
        "total",
        existing_type=sa.Numeric(10, 2),
        type_=sa.Numeric(),
        existing_nullable=True,
    )
