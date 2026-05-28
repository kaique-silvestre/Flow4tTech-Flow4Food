"""create assinaturas table

Revision ID: 0045
Revises: 0044
Create Date: 2026-05-28

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0045"
down_revision: Union[str, None] = "0044"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VALID_STATUS = ("trial", "ativa", "vencida", "cancelada", "suspensa")


def upgrade() -> None:
    op.create_table(
        "assinaturas",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.BigInteger(),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="trial"),
        sa.Column(
            "data_inicio",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("data_vencimento", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index("ix_assinaturas_status", "assinaturas", ["status"])
    op.create_index("ix_assinaturas_tenant_id", "assinaturas", ["tenant_id"])

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        bind.execute(
            sa.text(
                "ALTER TABLE assinaturas ADD CONSTRAINT ck_assinaturas_status "
                "CHECK (status IN ('trial', 'ativa', 'vencida', 'cancelada', 'suspensa'))"
            )
        )

    # Seed default tenant assinatura so tenant_id=1 has trial subscription
    bind.execute(
        sa.text(
            "INSERT INTO assinaturas (tenant_id, status) VALUES (1, 'trial') "
            "ON CONFLICT (tenant_id) DO NOTHING"
            if bind.dialect.name == "postgresql"
            else "INSERT OR IGNORE INTO assinaturas (tenant_id, status) VALUES (1, 'trial')"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_assinaturas_tenant_id", "assinaturas")
    op.drop_index("ix_assinaturas_status", "assinaturas")
    op.drop_table("assinaturas")
