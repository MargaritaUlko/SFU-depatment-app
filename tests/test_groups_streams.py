import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import make_headers
from app.users.model import Role

pytestmark = pytest.mark.asyncio


async def _create_stream(client, headers, name="ВЦ", year=2025, speciality="ВМиКН"):
    resp = await client.post(
        "/api/v1/streams",
        json={"name": name, "year": year, "speciality": speciality},
        headers=headers,
    )
    return resp.json()["id"]


async def test_create_stream(client: AsyncClient, db: AsyncSession):
    """Администратор создаёт поток."""
    headers = await make_headers(client, db, "sadmin@test.ru", Role.admin)
    resp = await client.post(
        "/api/v1/streams",
        json={"name": "ВЦ", "year": 2025, "speciality": "ВМиКН"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "ВЦ"
    assert "id" in data


async def test_list_streams(client: AsyncClient, db: AsyncSession):
    """Список потоков доступен авторизованному пользователю."""
    headers = await make_headers(client, db, "sadmin2@test.ru", Role.admin)
    await _create_stream(client, headers, "ИС", 2024, "Информатика")
    resp = await client.get("/api/v1/streams", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_create_group(client: AsyncClient, db: AsyncSession):
    """Администратор создаёт группу внутри потока."""
    headers = await make_headers(client, db, "gadmin2@test.ru", Role.admin)
    stream_id = await _create_stream(client, headers, "ВЦ2", 2025, "ВМиКН")
    resp = await client.post(
        "/api/v1/groups",
        json={"name": "ВЦ25-01", "stream_id": stream_id, "year": 2025},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "ВЦ25-01"


async def test_student_cannot_create_group(client: AsyncClient, db: AsyncSession):
    """Студент не может создавать группы."""
    headers = await make_headers(client, db, "sg@test.ru", Role.student)
    resp = await client.post(
        "/api/v1/groups",
        json={"name": "X", "stream_id": 1, "year": 2025},
        headers=headers,
    )
    assert resp.status_code == 403


async def test_get_group_by_id(client: AsyncClient, db: AsyncSession):
    """Получение группы по ID."""
    headers = await make_headers(client, db, "gadmin3@test.ru", Role.admin)
    stream_id = await _create_stream(client, headers, "КИ", 2026, "ПИ")
    create_resp = await client.post(
        "/api/v1/groups",
        json={"name": "КИ-01", "stream_id": stream_id, "year": 2026},
        headers=headers,
    )
    assert create_resp.status_code == 201
    group_id = create_resp.json()["id"]
    resp = await client.get(f"/api/v1/groups/{group_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == group_id
