from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "department",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.announcements.tasks"],
)

celery_app.conf.beat_schedule = {
    "sync-announcement-statuses": {
        "task": "app.announcements.tasks.sync_announcement_statuses",
        "schedule": crontab(),  # каждую минуту
    },
    "cleanup-archived-announcements": {
        "task": "app.announcements.tasks.cleanup_archived_announcements",
        "schedule": crontab(hour=3, minute=0),  # каждую ночь в 03:00 UTC
    },
}
celery_app.conf.timezone = "Asia/Krasnoyarsk"
celery_app.conf.enable_utc = True
