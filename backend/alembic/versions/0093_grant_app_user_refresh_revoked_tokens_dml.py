"""grant INSERT/UPDATE/DELETE on refresh_tokens and revoked_tokens to app_user

0050_create_app_user_role granted app_user only SELECT on refresh_tokens e
revoked_tokens (_READONLY_TABLES), mas o próprio fluxo de login/logout roda
sob app_user (auth_service.login chama arm() antes de criar o refresh token)
e precisa INSERT (criar refresh token, revogar token no logout) e DELETE
(limpeza de tokens expirados/revogados pelo scheduler). Sem isso, login falha
com "permission denied for table refresh_tokens" em qualquer banco criado do
zero — só não apareceu antes porque a suíte de testes roda em SQLite (RLS é
no-op lá) e o Postgres de dev/staging já tinha os grants aplicados manualmente
em algum momento fora de migration.

Revision ID: 0093
Revises: 0092
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0093"
down_revision: Union[str, None] = "0092"
branch_labels = None
depends_on = None

_TABLES = ["refresh_tokens", "revoked_tokens"]


def _role_exists(bind) -> bool:
    row = bind.execute(sa.text("SELECT 1 FROM pg_roles WHERE rolname = 'app_user'")).fetchone()
    return row is not None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql" or not _role_exists(bind):
        return

    for table in _TABLES:
        bind.execute(sa.text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {table} TO app_user"))


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql" or not _role_exists(bind):
        return

    for table in _TABLES:
        bind.execute(sa.text(f"REVOKE INSERT, UPDATE, DELETE ON TABLE {table} FROM app_user"))
