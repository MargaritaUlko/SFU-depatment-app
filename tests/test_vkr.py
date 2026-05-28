"""Тесты модуля управления темами ВКР."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_user_with_role, make_headers
from app.users.model import Role

pytestmark = pytest.mark.asyncio

_TOPIC = {"title": "Разработка REST API информационного портала кафедры", "description": "..."}


async def test_student_proposes_topic(client: AsyncClient, db: AsyncSession):
    """Студент подаёт заявку на тему ВКР."""
    headers = await make_headers(client, db, "st_vkr@test.ru", Role.student)
    resp = await client.post("/api/v1/vkr/topics", json=_TOPIC, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == _TOPIC["title"]
    assert data["status"] == "pending"


async def test_teacher_proposes_topic(client: AsyncClient, db: AsyncSession):
    """Преподаватель может подать заявку на тему."""
    headers = await make_headers(client, db, "t_vkr@test.ru", Role.teacher)
    resp = await client.post("/api/v1/vkr/topics", json=_TOPIC, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"


async def test_my_topics_list(client: AsyncClient, db: AsyncSession):
    """GET /vkr/my-topics возвращает заявки текущего пользователя."""
    headers = await make_headers(client, db, "st_vkr2@test.ru", Role.student)
    await client.post("/api/v1/vkr/topics", json=_TOPIC, headers=headers)
    resp = await client.get("/api/v1/vkr/my-topics", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_deputy_approves_topic(client: AsyncClient, db: AsyncSession):
    """Заместитель заведующего утверждает тему ВКР."""
    student_h = await make_headers(client, db, "st_vkr3@test.ru", Role.student)
    deputy_h = await make_headers(client, db, "dep_vkr@test.ru", Role.deputy_head)

    topic_id = (
        await client.post("/api/v1/vkr/topics", json=_TOPIC, headers=student_h)
    ).json()["id"]

    resp = await client.post(
        f"/api/v1/vkr/topics/{topic_id}/review",
        json={"approved": True, "comment": "Одобрено"},
        headers=deputy_h,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


async def test_deputy_rejects_topic(client: AsyncClient, db: AsyncSession):
    """Заместитель заведующего отклоняет тему с комментарием."""
    student_h = await make_headers(client, db, "st_vkr4@test.ru", Role.student)
    deputy_h = await make_headers(client, db, "dep_vkr2@test.ru", Role.deputy_head)

    topic_id = (
        await client.post("/api/v1/vkr/topics", json=_TOPIC, headers=student_h)
    ).json()["id"]

    resp = await client.post(
        f"/api/v1/vkr/topics/{topic_id}/review",
        json={"approved": False, "comment": "Тема слишком общая"},
        headers=deputy_h,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"
    assert resp.json()["head_comment"] == "Тема слишком общая"


async def test_student_cannot_review_topic(client: AsyncClient, db: AsyncSession):
    """Студент не может рецензировать темы ВКР."""
    student_h = await make_headers(client, db, "st_vkr5@test.ru", Role.student)
    topic_id = (
        await client.post("/api/v1/vkr/topics", json=_TOPIC, headers=student_h)
    ).json()["id"]

    other_student_h = await make_headers(client, db, "st_vkr6@test.ru", Role.student)
    resp = await client.post(
        f"/api/v1/vkr/topics/{topic_id}/review",
        json={"approved": True},
        headers=other_student_h,
    )
    assert resp.status_code == 403


async def test_approved_topics_visible_to_deputy(client: AsyncClient, db: AsyncSession):
    """Заместитель может видеть список одобренных тем."""
    student_h = await make_headers(client, db, "st_vkr7@test.ru", Role.student)
    deputy_h = await make_headers(client, db, "dep_vkr3@test.ru", Role.deputy_head)

    topic_id = (
        await client.post("/api/v1/vkr/topics", json=_TOPIC, headers=student_h)
    ).json()["id"]
    await client.post(
        f"/api/v1/vkr/topics/{topic_id}/review",
        json={"approved": True},
        headers=deputy_h,
    )

    resp = await client.get("/api/v1/vkr/topics/approved", headers=deputy_h)
    assert resp.status_code == 200
    assert any(t["id"] == topic_id for t in resp.json())
