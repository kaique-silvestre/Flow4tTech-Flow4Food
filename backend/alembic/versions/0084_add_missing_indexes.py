"""add missing indexes for itens_comanda, ficha_tecnica, eventos_comanda, comissoes_garcom, audit_logs

Revision ID: 0084
Revises: 0083
Create Date: 2026-08-20

"""

from typing import Sequence, Union

from alembic import op

revision: str = "0084"
down_revision: Union[str, None] = "0083"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_itens_comanda_comanda_id", "itens_comanda", ["comanda_id"])
    op.create_index("ix_ficha_tecnica_produto_id", "ficha_tecnica", ["produto_id"])
    op.create_index("ix_eventos_comanda_comanda_id", "eventos_comanda", ["comanda_id"])
    op.create_index("ix_comissoes_garcom_comanda_id", "comissoes_garcom", ["comanda_id"])
    op.create_index("ix_comissoes_garcom_garcom_id", "comissoes_garcom", ["garcom_id"])
    op.create_index("ix_audit_logs_tenant_id_created_at", "audit_logs", ["tenant_id", "created_at"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_tenant_id_created_at", table_name="audit_logs")
    op.drop_index("ix_comissoes_garcom_garcom_id", table_name="comissoes_garcom")
    op.drop_index("ix_comissoes_garcom_comanda_id", table_name="comissoes_garcom")
    op.drop_index("ix_eventos_comanda_comanda_id", table_name="eventos_comanda")
    op.drop_index("ix_ficha_tecnica_produto_id", table_name="ficha_tecnica")
    op.drop_index("ix_itens_comanda_comanda_id", table_name="itens_comanda")
