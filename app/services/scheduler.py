import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.session import AsyncSessionLocal
from app.models.announcement import Announcement, AnnouncementStatus
from app.services.announcement_service import notify_users_about_announcement

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


async def publish_scheduled_announcements():
    """Публикует объявления, у которых наступило время публикации."""
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(Announcement)
            .options(selectinload(Announcement.attachments))
            .where(
                Announcement.status == AnnouncementStatus.scheduled,
                Announcement.publish_at <= now,
            )
        )
        announcements = result.scalars().all()

        for ann in announcements:
            ann.status = AnnouncementStatus.published
            await db.commit()
            await notify_users_about_announcement(db, ann)
            logger.info(f"Опубликовано запланированное объявление #{ann.id}: {ann.title}")


def start_scheduler():
    scheduler.add_job(
        publish_scheduled_announcements,
        trigger="interval",
        minutes=1,
        id="publish_scheduled",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Планировщик запущен")


def stop_scheduler():
    scheduler.shutdown()