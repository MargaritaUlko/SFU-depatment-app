import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_credentials_email(to: str, full_name: str, password: str) -> None:
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY не настроен — письмо не отправлено (%s)", to)
        return

    body = (
        f"Здравствуйте, {full_name}!\n\n"
        f"Для вас создана учётная запись на портале кафедры.\n\n"
        f"Email: {to}\n"
        f"Пароль: {password}\n\n"
        f"Рекомендуем сменить пароль после первого входа."
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
            json={
                "from": settings.SMTP_FROM,
                "to": [to],
                "subject": "Ваши данные для входа в портал кафедры",
                "text": body,
            },
            timeout=10,
        )
        logger.info("Resend response %s: %s", response.status_code, response.text)
        response.raise_for_status()
