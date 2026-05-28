import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_user_with_role, make_headers
from app.users.model import Role

pytestmark = pytest.mark.asyncio

EVENT_PAYLOAD = {
    "title": "День открытых дверей",
    "annotation": "Ждём всех!",
    "starts_at": "2026-09-01T10:00:00Z",
    "ends_at": "2026-09-01T14:00:00Z",
}


async def test_create_event(client: AsyncClient, db: AsyncSession):
    """Преподаватель создаёт событие."""
    headers = await make_headers(client, db, "teacher@ev.ru", Role.teacher)
    resp = await client.post("/api/v1/events", json=EVENT_PAYLOAD, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "День открытых дверей"
    assert "id" in data


async def test_list_events(client: AsyncClient, db: AsyncSession):
    """Список событий доступен любому авторизованному пользователю."""
    headers = await make_headers(client, db, "teacher2@ev.ru", Role.teacher)
    await client.post("/api/v1/events", json=EVENT_PAYLOAD, headers=headers)
    resp = await client.get("/api/v1/events", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_get_event_by_id(client: AsyncClient, db: AsyncSession):
    """Получение одного события по ID."""
    headers = await make_headers(client, db, "teacher3@ev.ru", Role.teacher)
    event_id = (await client.post("/api/v1/events", json=EVENT_PAYLOAD, headers=headers)).json()["id"]
    resp = await client.get(f"/api/v1/events/{event_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == event_id


async def test_update_event(client: AsyncClient, db: AsyncSession):
    """Автор события может изменить его название."""
    headers = await make_headers(client, db, "teacher4@ev.ru", Role.teacher)
    event_id = (await client.post("/api/v1/events", json=EVENT_PAYLOAD, headers=headers)).json()["id"]
    resp = await client.put(
        f"/api/v1/events/{event_id}",
        json={"title": "Новое название"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Новое название"


async def test_delete_event(client: AsyncClient, db: AsyncSession):
    """Автор события может его удалить."""
    headers = await make_headers(client, db, "teacher5@ev.ru", Role.teacher)
    event_id = (await client.post("/api/v1/events", json=EVENT_PAYLOAD, headers=headers)).json()["id"]
    resp = await client.delete(f"/api/v1/events/{event_id}", headers=headers)
    assert resp.status_code == 204


async def test_get_nonexistent_event(client: AsyncClient, db: AsyncSession):
    """Запрос несуществующего события возвращает 404."""
    headers = await make_headers(client, db, "teacher6@ev.ru", Role.teacher)
    resp = await client.get("/api/v1/events/99999", headers=headers)
    assert resp.status_code == 404


async def test_student_cannot_create_event(client: AsyncClient, db: AsyncSession):
    """Студент не может создавать события — требуется роль teacher/headman/admin."""
    headers = await make_headers(client, db, "st@ev.ru", Role.student)
    resp = await client.post("/api/v1/events", json=EVENT_PAYLOAD, headers=headers)
    assert resp.status_code == 403


async def test_unauthenticated_cannot_list_events(client: AsyncClient, db: AsyncSession):
    """Без токена список событий недоступен (FastAPI OAuth2 возвращает 401 или 403)."""
    resp = await client.get("/api/v1/events")
    assert resp.status_code in (401, 403)
