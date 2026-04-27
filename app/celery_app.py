from celery import Celery
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
        "schedule": 60.0,  # каждые 60 секунд
    },
}
celery_app.conf.timezone = "UTC"
celery_app.conf.enable_utc = True
