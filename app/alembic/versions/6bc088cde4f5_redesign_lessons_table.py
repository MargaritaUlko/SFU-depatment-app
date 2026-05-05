"""redesign lessons table

Revision ID: 6bc088cde4f5
Revises: 5ac077bda3a8
Create Date: 2026-05-04 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "6bc088cde4f5"
down_revision: Union[str, None] = "5ac077bda3a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("group_lessons")
    op.drop_table("teacher_lessons")
    op.drop_table("lessons")

    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=True),
        sa.Column("teacher_name", sa.String(length=255), nullable=True),
        sa.Column("day", sa.Integer(), nullable=False),
        sa.Column("week", sa.Integer(), nullable=False),
        sa.Column("time_start", sa.String(length=10), nullable=False),
        sa.Column("time_end", sa.String(length=10), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("lesson_type", sa.String(length=100), nullable=True),
        sa.Column("room", sa.String(length=200), nullable=True),
        sa.Column("building", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "group_id", "day", "week", "time_start", "subject", name="uq_lesson"
        ),
    )


def downgrade() -> None:
    op.drop_table("lessons")

    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("day", sa.Integer(), nullable=False),
        sa.Column("week", sa.Integer(), nullable=False),
        sa.Column("time_start", sa.String(length=10), nullable=False),
        sa.Column("time_end", sa.String(length=10), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("place", sa.String(length=200), nullable=True),
        sa.Column("building", sa.String(length=200), nullable=True),
        sa.Column("room", sa.String(length=500), nullable=True),
        sa.Column("sync_type", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "teacher_lessons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("groups", sa.ARRAY(sa.Integer()), nullable=False),
        sa.ForeignKeyConstraint(["id"], ["lessons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "group_lessons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["id"], ["lessons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
