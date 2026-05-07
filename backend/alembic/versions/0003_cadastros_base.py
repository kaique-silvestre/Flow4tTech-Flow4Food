"""cadastros_base: categorias, fornecedores, garcons, metodos_pagamento + seed

Revision ID: 0003_cadastros_base
Revises: 0002_auth
Create Date: 2026-05-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_cadastros_base"
down_revision: Union[str, None] = "0002_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categorias",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome", sa.String, nullable=False, unique=True),
    )
    op.create_table(
        "fornecedores",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome", sa.String, nullable=False),
        sa.Column("telefone", sa.String, nullable=True),
        sa.Column("email", sa.String, nullable=True),
    )
    op.create_table(
        "garcons",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome", sa.String, nullable=False),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default="true"),
    )
    op.create_table(
        "metodos_pagamento",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome", sa.String, nullable=False, unique=True),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default="true"),
    )

    op.execute(
        "INSERT INTO categorias (nome) VALUES ('Geral') ON CONFLICT (nome) DO NOTHING"
    )
    op.execute(
        "INSERT INTO metodos_pagamento (nome, ativo) VALUES "
        "('PIX', true), ('Crédito', true), ('Débito', true), ('Dinheiro', true) "
        "ON CONFLICT (nome) DO NOTHING"
    )


def downgrade() -> None:
    op.drop_table("metodos_pagamento")
    op.drop_table("garcons")
    op.drop_table("fornecedores")
    op.drop_table("categorias")
