import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import create_user_with_role
from app.users.model import Role

pytestmark = pytest.mark.asyncio


async def _admin_headers(client: AsyncClient, db: AsyncSession, email: str = "gadmin@test.ru") -> dict:
    await create_user_with_role(db, email, Role.admin)
    resp = await client.post("/api/v1/auth/login", data={"username": email, "password": "pass"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def test_create_stream(client: AsyncClient, db: AsyncSession):
    headers = await _admin_headers(client, db, "sadmin@test.ru")
    resp = await client.post("/api/v1/streams", json={
        "name": "ВЦ", "year": 2025, "speciality": "ВМиКН",
    }, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "ВЦ"
    assert "id" in data


async def test_list_streams(client: AsyncClient, db: AsyncSession):
    headers = await _admin_headers(client, db, "sadmin2@test.ru")
    await client.post("/api/v1/streams", json={
        "name": "ИС", "year": 2024, "speciality": "Информатика",
    }, headers=headers)
    resp = await client.get("/api/v1/streams", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_create_group(client: AsyncClient, db: AsyncSession):
    headers = await _admin_headers(client, db, "gadmin2@test.ru")
    stream_resp = await client.post("/api/v1/streams", json={
        "name": "ВЦ2", "year": 2025, "speciality": "ВМиКН",
    }, headers=headers)
    stream_id = stream_resp.json()["id"]

    resp = await client.post("/api/v1/groups", json={
        "name": "ВЦ25-01",
        "stream_id": stream_id,
        "year": 2025,
        "sfu_timetable_name": "ВЦ25-01 (1 подгруппа)",
    }, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["sfu_timetable_name"] == "ВЦ25-01 (1 подгруппа)"


async def test_student_cannot_create_group(client: AsyncClient, db: AsyncSession):
    await create_user_with_role(db, "sg@test.ru", Role.student)
    resp = await client.post("/api/v1/auth/login", data={"username": "sg@test.ru", "password": "pass"})
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    resp2 = await client.post("/api/v1/groups", json={
        "name": "X", "year": 2025, "sfu_timetable_name": "X",
    }, headers=headers)
    assert resp2.status_code == 403
