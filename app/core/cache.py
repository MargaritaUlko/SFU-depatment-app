from cachetools import TTLCache
from app.core.config import settings

# Singleton cache for schedule data
schedule_cache: TTLCache = TTLCache(
    maxsize=settings.SCHEDULE_CACHE_SIZE,
    ttl=settings.SCHEDULE_CACHE_TTL,
)
