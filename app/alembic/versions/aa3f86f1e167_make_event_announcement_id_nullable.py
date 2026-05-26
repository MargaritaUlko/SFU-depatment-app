"""make_event_announcement_id_nullable

Revision ID: aa3f86f1e167
Revises: b3c4d5e6f7a8
Create Date: 2026-05-11 17:40:09.771634

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "aa3f86f1e167"
down_revision: Union[str, None] = "b3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "events", "announcement_id", existing_type=sa.INTEGER(), nullable=True
    )
    op.drop_constraint("events_announcement_id_fkey", "events", type_="foreignkey")
    op.create_foreign_key(
        "events_announcement_id_fkey",
        "events",
        "announcements",
        ["announcement_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("events_announcement_id_fkey", "events", type_="foreignkey")
    op.create_foreign_key(
        "events_announcement_id_fkey",
        "events",
        "announcements",
        ["announcement_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.execute("DELETE FROM events WHERE announcement_id IS NULL")
    op.alter_column(
        "events", "announcement_id", existing_type=sa.INTEGER(), nullable=False
    )
