import logging
from datetime import date, datetime, timedelta, timezone

from arq.connections import RedisSettings
from arq.cron import cron
from sqlalchemy import select, update

from app.announcements.model import Announcement, AnnouncementStatus
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.groups.model import Group

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


async def sync_lessons_for_all_groups(ctx: dict) -> None:
    """Каждое воскресенье синхронизирует пары на следующие 2 недели."""
    today = date.today()
    date_from = today
    date_to = today + timedelta(weeks=2)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Group))
        groups = result.scalars().all()
        for group in groups:
            try:
                count = await sync_lessons(
                    db,
                    group_id=group.id,
                    sfu_group_name=group.name,
                    date_from=date_from,
                    date_to=date_to,
                )
                if count:
                    logger.info("Группа %s: синхронизировано %d пар", group.name, count)
            except Exception as e:
                logger.warning("Группа %s: ошибка синхронизации — %s", group.name, e)


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    cron_jobs = [
        cron(sync_announcement_statuses, second=0),  # каждую минуту
        cron(sync_lessons_for_all_groups, weekday=6, hour=3, minute=0),  # вс 03:00
    ]
