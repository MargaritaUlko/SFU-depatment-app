import logging

from fastapi import HTTPException, Request, status

from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)

# Защита логина от подбора пароля
LOGIN_FAIL_LIMIT = 5
LOGIN_FAIL_WINDOW_SECONDS = 15 * 60
LOGIN_LOCK_SECONDS = 15 * 60


def client_ip(request: Request) -> str:
    # Nginx перезаписывает X-Real-IP через proxy_set_header, поэтому подделать
    # его с клиента нельзя. X-Forwarded-For nginx не выставляет — доверять ему
    # нельзя, клиент может прислать любое значение.
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


async def enforce_rate_limit(
    key: str,
    limit: int,
    window_seconds: int,
    message: str = "Слишком много запросов. Попробуйте позже.",
) -> None:
    """Fixed-window лимит запросов на Redis.

    Если Redis недоступен — fail-open (запрос пропускается), чтобы сбой
    кэша не блокировал вход в систему. Ловим любые исключения намеренно:
    rate limiter не должен становиться точкой отказа для аутентификации.
    """
    try:
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, window_seconds)
    except Exception:
        logger.warning("Redis недоступен, rate limit для '%s' пропущен", key)
        return

    if count > limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message)


def _login_fail_key(email: str) -> str:
    return f"login_fail:{email.strip().lower()}"


def _login_lock_key(email: str) -> str:
    return f"login_lock:{email.strip().lower()}"


async def is_login_locked(email: str) -> bool:
    try:
        return bool(await redis_client.exists(_login_lock_key(email)))
    except Exception:
        logger.warning("Redis недоступен, проверка блокировки логина пропущена")
        return False


async def register_failed_login(email: str) -> None:
    try:
        key = _login_fail_key(email)
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, LOGIN_FAIL_WINDOW_SECONDS)
        if count >= LOGIN_FAIL_LIMIT:
            await redis_client.set(_login_lock_key(email), "1", ex=LOGIN_LOCK_SECONDS)
    except Exception:
        logger.warning("Redis недоступен, счётчик неудачных входов не обновлён")


async def reset_failed_login(email: str) -> None:
    try:
        await redis_client.delete(_login_fail_key(email), _login_lock_key(email))
    except Exception:
        pass
