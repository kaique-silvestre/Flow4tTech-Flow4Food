"""add valor_nota and troco to pagamentos

Revision ID: 0028_add_troco_pagamento
Revises: 0027_add_tipo_metodo_pagamento
Create Date: 2026-05-13
"""

from alembic import op
import sqlalchemy as sa

revision = "0028_add_troco_pagamento"
down_revision = "0027_add_tipo_metodo_pagamento"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("pagamentos", sa.Column("valor_nota", sa.Numeric(10, 2), nullable=True))
    op.add_column("pagamentos", sa.Column("troco", sa.Numeric(10, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("pagamentos", "troco")
    op.drop_column("pagamentos", "valor_nota")
