"""add tipo to metodos_pagamento

Revision ID: 0027_add_tipo_metodo_pagamento
Revises: 0026_fornecedor_ativo
Create Date: 2026-05-13
"""

from alembic import op
import sqlalchemy as sa

revision = "0027_add_tipo_metodo_pagamento"
down_revision = "0026_fornecedor_ativo"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "metodos_pagamento",
        sa.Column(
            "tipo",
            sa.String(),
            nullable=False,
            server_default="outro",
        ),
    )


def downgrade() -> None:
    op.drop_column("metodos_pagamento", "tipo")
