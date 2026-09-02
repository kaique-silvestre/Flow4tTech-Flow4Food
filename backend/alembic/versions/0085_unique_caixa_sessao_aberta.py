"""unique index preventing more than one open caixa sessao per tenant

Revision ID: 0085
Revises: 0084
Create Date: 2026-08-20

Idempotente de propósito: a migration 0044 (create_caixa) já cria este mesmo
índice desde a origem, então num banco novo (upgrade head do zero) 0044 e
0085 tentavam criar `uq_caixa_sessoes_tenant_aberta` duas vezes, quebrando
`alembic upgrade head`. Usa IF NOT EXISTS/IF EXISTS pra funcionar tanto em
bancos que já têm o índice (criado por 0044) quanto nos que não têm.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0085"
down_revision: Union[str, None] = "0084"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_caixa_sessoes_tenant_aberta "
            "ON caixa_sessoes (tenant_id) WHERE status = 'aberta'"
        )


def downgrade() -> None:
    # No-op: dropping here would break databases where 0044 (not this
    # migration) is the one that created the index. 0044's own downgrade
    # already drops it.
    pass
