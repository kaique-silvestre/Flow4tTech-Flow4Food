"""initial empty

Revision ID: 0001_initial_empty
Revises:
Create Date: 2026-05-06

"""
from typing import Sequence, Union

revision: str = "0001_initial_empty"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
