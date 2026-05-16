"""fix chat timestamp defaults

Revision ID: d1e2f3a4b5c6
Revises: aa3f86f1e167
Create Date: 2026-05-15

"""
import sqlalchemy as sa
from alembic import op

revision = 'd1e2f3a4b5c6'
down_revision = 'aa3f86f1e167'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('chats', 'created_at', server_default=sa.func.now())
    op.alter_column('chats', 'updated_at', server_default=sa.func.now())
    op.alter_column('chat_messages', 'created_at', server_default=sa.func.now())
    op.alter_column('chat_messages', 'updated_at', server_default=sa.func.now())


def downgrade() -> None:
    op.alter_column('chat_messages', 'updated_at', server_default=None)
    op.alter_column('chat_messages', 'created_at', server_default=None)
    op.alter_column('chats', 'updated_at', server_default=None)
    op.alter_column('chats', 'created_at', server_default=None)
