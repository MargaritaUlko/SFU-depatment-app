"""add avatar to users

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-05-16

"""
import sqlalchemy as sa
from alembic import op

revision = 'e2f3a4b5c6d7'
down_revision = 'd1e2f3a4b5c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('avatar', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'avatar')
