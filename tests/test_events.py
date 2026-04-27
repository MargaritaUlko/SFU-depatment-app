import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import create_user_with_role
from app.users.model import Role

pytestmark = pytest.mark.asyncio

EVENT_PAYLOAD = {
    "title": "День открытых дверей",
    "annotation": "Ждём всех!",
    "starts_at": "2026-04-01T10:00:00Z",
    "ends_at": "2026-04-01T14:00:00Z",
    "location": "Корпус №80",
    "links": [{"title": "Сайт", "url": "https://sfu-kras.ru"}],
}


async def _teacher_headers(client: AsyncClient, db: AsyncSession, email: str = "teacher@ev.ru") -> dict:
    await create_user_with_role(db, email, Role.teacher)
    resp = await client.post("/api/v1/auth/login", data={"username": email, "password": "pass"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def test_create_event(client: AsyncClient, db: AsyncSession):
    headers = await _teacher_headers(client, db)
    resp = await client.post("/api/v1/events", json=EVENT_PAYLOAD, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "День открытых дверей"
    assert len(data["links"]) == 1


async def test_list_events(client: AsyncClient, db: AsyncSession):
    headers = await _teacher_headers(client, db, "teacher2@ev.ru")
    await client.post("/api/v1/events", json=EVENT_PAYLOAD, headers=headers)
    resp = await client.get("/api/v1/events", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_get_event(client: AsyncClient, db: AsyncSession):
    headers = await _teacher_headers(client, db, "teacher3@ev.ru")
    create_resp = await client.post("/api/v1/events", json=EVENT_PAYLOAD, headers=headers)
    event_id = create_resp.json()["id"]
    resp = await client.get(f"/api/v1/events/{event_id}", headers=headers)
    assert resp.status_code == 200


async def test_update_event(client: AsyncClient, db: AsyncSession):
    headers = await _teacher_headers(client, db, "teacher4@ev.ru")
    create_resp = await client.post("/api/v1/events", json=EVENT_PAYLOAD, headers=headers)
    event_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/v1/events/{event_id}",
        json={"title": "Новое название"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Новое название"


async def test_delete_event(client: AsyncClient, db: AsyncSession):
    headers = await _teacher_headers(client, db, "teacher5@ev.ru")
    create_resp = await client.post("/api/v1/events", json=EVENT_PAYLOAD, headers=headers)
    event_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/v1/events/{event_id}", headers=headers)
    assert resp.status_code == 204


async def test_student_cannot_create_event(client: AsyncClient, db: AsyncSession):
    await create_user_with_role(db, "st@ev.ru", Role.student)
    resp = await client.post("/api/v1/auth/login", data={"username": "st@ev.ru", "password": "pass"})
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    resp2 = await client.post("/api/v1/events", json=EVENT_PAYLOAD, headers=headers)
    assert resp2.status_code == 403
