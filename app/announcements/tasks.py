import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

import app.db.models  # noqa: F401 — registers all mappers before relationship resolution
from app.announcements.model import Announcement, AnnouncementStatus
from app.celery_app import celery_app
from app.core.config import settings

logger = logging.getLogger(__name__)


async def _sync_statuses() -> None:
    # NullPool — обязательно для Celery: каждая задача создаёт свой event loop,
    # пул соединений asyncpg к нему не привязывается
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    now = datetime.now(timezone.utc)
    async with Session() as db:
        published = await db.execute(
            update(Announcement)
            .where(
                Announcement.status == AnnouncementStatus.scheduled,
                Announcement.publish_at <= now,
            )
            .values(status=AnnouncementStatus.published)
        )
        archived = await db.execute(
            update(Announcement)
            .where(
                Announcement.status == AnnouncementStatus.published,
                Announcement.expires_at.isnot(None),
                Announcement.expires_at <= now,
            )
            .values(status=AnnouncementStatus.archived)
        )
        await db.commit()

    await engine.dispose()

    if published.rowcount:
        logger.info("Опубликовано объявлений: %d", published.rowcount)
    if archived.rowcount:
        logger.info("Архивировано объявлений: %d", archived.rowcount)


@celery_app.task(name="app.announcements.tasks.sync_announcement_statuses")
def sync_announcement_statuses() -> None:
    asyncio.run(_sync_statuses())
