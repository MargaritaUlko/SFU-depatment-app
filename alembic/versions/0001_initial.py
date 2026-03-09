"""Initial migration: all tables

Revision ID: 0001
Revises:
Create Date: 2026-03-08
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаём PostgreSQL enum-типы через raw DDL (идемпотентно через DO-блок)
    op.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE role AS ENUM ('student', 'teacher', 'head', 'admin');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """))
    op.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE targettype AS ENUM ('group', 'stream');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """))

    op.execute(sa.text("""
        CREATE TABLE users (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email       VARCHAR(255) NOT NULL UNIQUE,
            full_name   VARCHAR(255) NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            role        role NOT NULL DEFAULT 'student',
            is_active   BOOLEAN NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    op.execute(sa.text("CREATE INDEX ix_users_email ON users (email)"))

    op.execute(sa.text("""
        CREATE TABLE refresh_tokens (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            jti         VARCHAR(36) NOT NULL UNIQUE,
            user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expires_at  TIMESTAMPTZ NOT NULL,
            revoked     BOOLEAN NOT NULL DEFAULT FALSE
        )
    """))
    op.execute(sa.text("CREATE INDEX ix_refresh_tokens_jti ON refresh_tokens (jti)"))

    op.execute(sa.text("""
        CREATE TABLE streams (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name        VARCHAR(100) NOT NULL,
            year        INTEGER NOT NULL,
            speciality  VARCHAR(255) NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))

    op.execute(sa.text("""
        CREATE TABLE groups (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name                VARCHAR(100) NOT NULL,
            stream_id           UUID REFERENCES streams(id) ON DELETE SET NULL,
            year                INTEGER NOT NULL,
            sfu_timetable_name  VARCHAR(255) NOT NULL,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))

    op.execute(sa.text("""
        CREATE TABLE messages (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            sender_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            target_type targettype NOT NULL,
            target_id   UUID NOT NULL,
            subject     VARCHAR(255) NOT NULL,
            body        TEXT NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))

    op.execute(sa.text("""
        CREATE TABLE events (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title       VARCHAR(255) NOT NULL,
            annotation  TEXT,
            starts_at   TIMESTAMPTZ NOT NULL,
            ends_at     TIMESTAMPTZ NOT NULL,
            location    VARCHAR(255),
            image_url   VARCHAR(500),
            creator_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))

    op.execute(sa.text("""
        CREATE TABLE event_links (
            id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
            title    VARCHAR(255) NOT NULL,
            url      VARCHAR(500) NOT NULL
        )
    """))

    op.execute(sa.text("""
        CREATE TABLE documents (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title       VARCHAR(255) NOT NULL,
            description TEXT,
            category    VARCHAR(100) NOT NULL,
            visibility  JSONB NOT NULL DEFAULT '[]',
            file_path   VARCHAR(500) NOT NULL,
            file_name   VARCHAR(255) NOT NULL,
            uploader_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS documents CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS event_links CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS events CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS messages CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS groups CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS streams CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS refresh_tokens CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS users CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS targettype CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS role CASCADE"))
