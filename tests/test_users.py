import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import create_user_with_role
from app.users.model import Role

pytestmark = pytest.mark.asyncio


async def _login(client: AsyncClient, db: AsyncSession, email: str, role: Role = Role.student) -> dict:
    await create_user_with_role(db, email, role)
    resp = await client.post("/api/v1/auth/login", data={"username": email, "password": "pass"})
    return resp.json()


async def test_get_users_requires_head_or_admin(client: AsyncClient, db: AsyncSession):
    tokens = await _login(client, db, "student_u@test.ru", Role.student)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.get("/api/v1/users", headers=headers)
    assert resp.status_code == 403


async def test_admin_can_list_users(client: AsyncClient, db: AsyncSession):
    tokens = await _login(client, db, "admin_u@test.ru", Role.admin)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.get("/api/v1/users", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_get_own_profile(client: AsyncClient, db: AsyncSession):
    tokens = await _login(client, db, "profile@test.ru", Role.teacher)
    admin_tokens = await _login(client, db, "adm2@test.ru", Role.admin)
    headers_admin = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    users = (await client.get("/api/v1/users", headers=headers_admin)).json()
    user = next((u for u in users if u["email"] == "profile@test.ru"), None)
    assert user is not None

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.get(f"/api/v1/users/{user['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "profile@test.ru"


async def test_admin_can_change_role(client: AsyncClient, db: AsyncSession):
    await create_user_with_role(db, "s2@test.ru", Role.student)
    admin_tokens = await _login(client, db, "adm3@test.ru", Role.admin)
    headers_admin = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    users = (await client.get("/api/v1/users", headers=headers_admin)).json()
    user = next((u for u in users if u["email"] == "s2@test.ru"), None)

    resp = await client.patch(
        f"/api/v1/users/{user['id']}/role",
        json={"role": "teacher"},
        headers=headers_admin,
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "teacher"
