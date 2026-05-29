"""fix dean_profiles columns

Revision ID: c1d2e3f4a5b6
Revises: 019304363317
Create Date: 2026-05-29 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, None] = "019304363317"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE dean_profiles ADD COLUMN IF NOT EXISTS user_id INTEGER")
    op.execute("ALTER TABLE dean_profiles ADD COLUMN IF NOT EXISTS faculty VARCHAR(255)")
    op.execute("ALTER TABLE dean_profiles ADD COLUMN IF NOT EXISTS position VARCHAR(255)")
    op.execute("ALTER TABLE dean_profiles ADD COLUMN IF NOT EXISTS phone VARCHAR(20)")
    op.execute("ALTER TABLE dean_profiles ADD COLUMN IF NOT EXISTS cabinet VARCHAR(50)")

    op.execute("UPDATE dean_profiles SET faculty = '' WHERE faculty IS NULL")
    op.execute("ALTER TABLE dean_profiles ALTER COLUMN faculty SET NOT NULL")

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'dean_profiles_user_id_fkey'
                  AND table_name = 'dean_profiles'
            ) THEN
                ALTER TABLE dean_profiles
                    ADD CONSTRAINT dean_profiles_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES users(id);
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'dean_profiles_user_id_key'
                  AND table_name = 'dean_profiles'
            ) THEN
                ALTER TABLE dean_profiles
                    ADD CONSTRAINT dean_profiles_user_id_key UNIQUE (user_id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.drop_constraint("dean_profiles_user_id_key", "dean_profiles", type_="unique")
    op.drop_constraint("dean_profiles_user_id_fkey", "dean_profiles", type_="foreignkey")
    op.drop_column("dean_profiles", "cabinet")
    op.drop_column("dean_profiles", "phone")
    op.drop_column("dean_profiles", "position")
    op.drop_column("dean_profiles", "faculty")
    op.drop_column("dean_profiles", "user_id")
