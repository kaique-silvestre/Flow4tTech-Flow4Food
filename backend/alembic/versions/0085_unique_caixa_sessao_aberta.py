"""unique index preventing more than one open caixa sessao per tenant

Revision ID: 0085
Revises: 0084
Create Date: 2026-08-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0085"
down_revision: Union[str, None] = "0084"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.create_index(
            "uq_caixa_sessoes_tenant_aberta",
            "caixa_sessoes",
            ["tenant_id"],
            unique=True,
            postgresql_where=sa.text("status = 'aberta'"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_index("uq_caixa_sessoes_tenant_aberta", table_name="caixa_sessoes")
