"""adiciona coluna ativo em promocoes

Pausar uma promocao exigia deleta-la, perdendo config e historico.
Adiciona flag ativo (default true) para soft-pause; a resolucao de
promocao em comandas_service.resolve_promo passa a filtrar por
ativo = true.

Revision ID: 0088
Revises: 0087
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0088"
down_revision: Union[str, None] = "0087"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "promocoes",
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("promocoes", "ativo")
