"""Тесты модуля объявлений."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import make_headers
from app.users.model import Role

pytestmark = pytest.mark.asyncio

_ANN = {"title": "Важное объявление", "content": "Текст объявления"}


async def test_teacher_creates_announcement(client: AsyncClient, db: AsyncSession):
    """Преподаватель может создать объявление."""
    headers = await make_headers(client, db, "t_ann@test.ru", Role.teacher)
    resp = await client.post("/api/v1/announcements", json=_ANN, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Важное объявление"
    assert data["status"] == "draft"


async def test_student_cannot_create_announcement(client: AsyncClient, db: AsyncSession):
    """Студент не может создавать объявления."""
    headers = await make_headers(client, db, "st_ann@test.ru", Role.student)
    resp = await client.post("/api/v1/announcements", json=_ANN, headers=headers)
    assert resp.status_code == 403


async def test_list_announcements(client: AsyncClient, db: AsyncSession):
    """Список объявлений доступен авторизованному пользователю."""
    headers = await make_headers(client, db, "t_ann2@test.ru", Role.teacher)
    await client.post("/api/v1/announcements", json=_ANN, headers=headers)
    resp = await client.get("/api/v1/announcements", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_get_announcement_by_id(client: AsyncClient, db: AsyncSession):
    """Получение объявления по ID."""
    headers = await make_headers(client, db, "t_ann3@test.ru", Role.teacher)
    ann_id = (await client.post("/api/v1/announcements", json=_ANN, headers=headers)).json()["id"]
    resp = await client.get(f"/api/v1/announcements/{ann_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == ann_id


async def test_update_announcement(client: AsyncClient, db: AsyncSession):
    """Автор может обновить заголовок объявления."""
    headers = await make_headers(client, db, "t_ann4@test.ru", Role.teacher)
    ann_id = (await client.post("/api/v1/announcements", json=_ANN, headers=headers)).json()["id"]
    resp = await client.patch(
        f"/api/v1/announcements/{ann_id}",
        json={"title": "Обновлённый заголовок"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Обновлённый заголовок"


async def test_delete_announcement(client: AsyncClient, db: AsyncSession):
    """Автор может удалить своё объявление."""
    headers = await make_headers(client, db, "t_ann5@test.ru", Role.teacher)
    ann_id = (await client.post("/api/v1/announcements", json=_ANN, headers=headers)).json()["id"]
    resp = await client.delete(f"/api/v1/announcements/{ann_id}", headers=headers)
    assert resp.status_code == 204


async def test_my_announcements(client: AsyncClient, db: AsyncSession):
    """GET /announcements/my возвращает объявления текущего пользователя."""
    headers = await make_headers(client, db, "t_ann6@test.ru", Role.teacher)
    await client.post("/api/v1/announcements", json=_ANN, headers=headers)
    resp = await client.get("/api/v1/announcements/my", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_get_nonexistent_announcement(client: AsyncClient, db: AsyncSession):
    """Запрос несуществующего объявления возвращает 404."""
    headers = await make_headers(client, db, "t_ann7@test.ru", Role.teacher)
    resp = await client.get("/api/v1/announcements/99999", headers=headers)
    assert resp.status_code == 404
