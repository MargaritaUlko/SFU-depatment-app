import httpx
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class MaxBotClient:
    """
    Клиент для VK Max Bot API.
    Документация: https://dev.max.ru/
    """

    def __init__(self):
        self.token = settings.MAX_BOT_TOKEN
        self.base_url = settings.MAX_BOT_API_URL

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def send_message(self, user_id: str, text: str) -> bool:
        """Отправить личное сообщение пользователю в Max."""
        if not self.token:
            logger.warning("MAX_BOT_TOKEN не задан, уведомление не отправлено")
            return False

        url = f"{self.base_url}/messages/send"
        payload = {
            "recipient": {"user_id": user_id},
            "text": text,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=self._headers)
                resp.raise_for_status()
                logger.info(f"Max уведомление отправлено пользователю {user_id}")
                return True
        except httpx.HTTPError as e:
            logger.error(f"Ошибка отправки в Max: {e}")
            return False

    async def send_announcement_notification(
        self,
        user_max_id: str,
        announcement_title: str,
        announcement_id: int,
        target_group: Optional[str] = None,
    ) -> bool:
        group_info = f" (группа: {target_group})" if target_group else ""
        text = (
            f"📢 Новое объявление{group_info}\n\n"
            f"**{announcement_title}**\n\n"
            f"Подробнее: /announcement/{announcement_id}"
        )
        return await self.send_message(user_max_id, text)

    async def send_attendance_notification(
        self,
        teacher_max_id: str,
        starosta_name: str,
        subject: str,
        group_name: str,
        present_count: int,
        total_students: int,
        report_id: int,
    ) -> bool:
        text = (
            f"📋 Список присутствующих\n\n"
            f"Предмет: {subject}\n"
            f"Группа: {group_name}\n"
            f"Присутствует: {present_count}/{total_students}\n"
            f"Отправил: {starosta_name}\n\n"
            f"Посмотреть отчёт: /attendance/{report_id}"
        )
        return await self.send_message(teacher_max_id, text)


max_bot = MaxBotClient()