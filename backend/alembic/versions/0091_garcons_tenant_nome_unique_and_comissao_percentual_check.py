"""garcons.nome per-tenant unique constraint; comissoes_garcom.percentual check

Revision ID: 0091
Revises: 0090
Create Date: 2026-09-01

Auditoria do módulo de comissões de garçom apontou duas lacunas:

1. garcons.nome não tinha nenhuma restrição de unicidade (a migration 0003
   original criou a coluna sem `unique=True`, diferente de categorias e
   metodos_pagamento). Isso permitia cadastrar dois garçons com o mesmo nome
   no mesmo tenant sem aviso. Segue o mesmo padrão adotado em 0082 para
   categorias/insumos/system_users: UNIQUE(tenant_id, nome), permitindo que
   tenants diferentes usem o mesmo nome sem colisão.

2. comissoes_garcom.percentual não tinha CheckConstraint no banco (0-100) —
   defesa em profundidade ausente contra valores inválidos gravados por
   fora da camada de aplicação.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0091"
down_revision: Union[str, None] = "0090"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint("uq_garcons_tenant_nome", "garcons", ["tenant_id", "nome"])
    op.create_check_constraint(
        "ck_comissoes_garcom_percentual_range",
        "comissoes_garcom",
        "percentual >= 0 AND percentual <= 100",
    )


def downgrade() -> None:
    op.drop_constraint("ck_comissoes_garcom_percentual_range", "comissoes_garcom", type_="check")
    op.drop_constraint("uq_garcons_tenant_nome", "garcons", type_="unique")
