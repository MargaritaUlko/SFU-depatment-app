from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import settings


async def send_credentials_email(to: str, full_name: str, password: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Ваши данные для входа в портал кафедры"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to

    body = (
        f"Здравствуйте, {full_name}!\n\n"
        f"Для вас создана учётная запись на портале кафедры.\n\n"
        f"Email: {to}\n"
        f"Пароль: {password}\n\n"
        f"Рекомендуем сменить пароль после первого входа."
    )
    msg.attach(MIMEText(body, "plain", "utf-8"))

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
    )
