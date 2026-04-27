import logging
from datetime import datetime, timezone

from arq.connections import RedisSettings
from arq.cron import cron
from sqlalchemy import update

from app.announcements.model import Announcement, AnnouncementStatus
from app.core.config import settings
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def sync_announcement_statuses(ctx: dict) -> None:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
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

    if published.rowcount:
        logger.info("Опубликовано объявлений: %d", published.rowcount)
    if archived.rowcount:
        logger.info("Архивировано объявлений: %d", archived.rowcount)


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    cron_jobs = [
        cron(sync_announcement_statuses, second=0),  # каждую минуту
    ]
