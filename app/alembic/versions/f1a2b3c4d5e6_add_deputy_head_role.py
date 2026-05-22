"""add deputy_head to role enum

Revision ID: f1a2b3c4d5e6
Revises: aa3f86f1e167
Create Date: 2026-05-22 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "e2f3a4b5c6d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE role ADD VALUE IF NOT EXISTS 'deputy_head'")


def downgrade() -> None:
    pass
