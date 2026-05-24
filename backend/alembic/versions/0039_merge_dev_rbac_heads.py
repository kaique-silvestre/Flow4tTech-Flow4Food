"""merge development and rbac migration heads

Revision ID: 0039
Revises: 0036a, 0038
Create Date: 2026-05-22

"""

from typing import Sequence, Union

revision: str = "0039"
down_revision: Union[str, tuple[str, ...], None] = ("0036a", "0038")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
