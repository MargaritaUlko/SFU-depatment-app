import logging
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


async def _send_email(to: str, subject: str, body: str) -> None:
    if not settings.SMTP_HOST:
        logger.warning("SMTP_HOST не настроен — письмо не отправлено (%s)", to)
        return
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
    )
    logger.info("Письмо отправлено: %s -> %s", settings.SMTP_FROM, to)


async def send_credentials_email(to: str, full_name: str, password: str) -> None:
    body = (
        f"Здравствуйте, {full_name}!\n\n"
        f"Для вас создана учётная запись на портале кафедры.\n\n"
        f"Email: {to}\n"
        f"Пароль: {password}\n\n"
        f"Рекомендуем сменить пароль после первого входа."
    )
    await _send_email(to, "Ваши данные для входа в портал кафедры", body)


async def send_password_reset_email(to: str, full_name: str, password: str) -> None:
    body = (
        f"Здравствуйте, {full_name}!\n\n"
        f"Поступил запрос на сброс пароля для вашей учётной записи.\n\n"
        f"Новый пароль: {password}\n\n"
        f"Если вы не запрашивали сброс пароля — немедленно смените пароль в личном кабинете."
    )
    await _send_email(to, "Сброс пароля на портале кафедры", body)
