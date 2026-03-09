import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _login(client, email, role="teacher"):
    await client.post("/api/v1/auth/register", json={
        "full_name": "U", "email": email, "password": "pass", "role": role,
    })
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "pass"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def _create_group(client, admin_headers):
    resp = await client.post("/api/v1/groups", json={
        "name": "ВЦ25-01", "year": 2025, "sfu_timetable_name": "ВЦ25-01",
    }, headers=admin_headers)
    return resp.json()["id"]


async def test_teacher_sends_message(client: AsyncClient):
    teacher_h = await _login(client, "t_msg@test.ru", "teacher")
    admin_h = await _login(client, "a_msg@test.ru", "admin")
    group_id = await _create_group(client, admin_h)

    resp = await client.post("/api/v1/messages", json={
        "target_type": "group",
        "target_id": group_id,
        "subject": "Тест",
        "body": "Привет, группа!",
    }, headers=teacher_h)
    assert resp.status_code == 201
    assert resp.json()["subject"] == "Тест"


async def test_student_cannot_send_message(client: AsyncClient):
    student_h = await _login(client, "st_msg@test.ru", "student")
    resp = await client.post("/api/v1/messages", json={
        "target_type": "group",
        "target_id": "00000000-0000-0000-0000-000000000001",
        "subject": "X",
        "body": "Y",
    }, headers=student_h)
    assert resp.status_code == 403


async def test_teacher_sees_own_messages(client: AsyncClient):
    t_h = await _login(client, "t2_msg@test.ru", "teacher")
    admin_h = await _login(client, "a2_msg@test.ru", "admin")
    group_id = await _create_group(client, admin_h)

    await client.post("/api/v1/messages", json={
        "target_type": "group", "target_id": group_id,
        "subject": "Mine", "body": "body",
    }, headers=t_h)

    resp = await client.get("/api/v1/messages", headers=t_h)
    assert resp.status_code == 200
    assert any(m["subject"] == "Mine" for m in resp.json())
