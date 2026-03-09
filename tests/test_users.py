import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _register_and_login(client: AsyncClient, email: str, role: str = "student") -> dict:
    await client.post("/api/v1/auth/register", json={
        "full_name": "User", "email": email, "password": "pass", "role": role,
    })
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "pass"})
    return resp.json()


async def test_get_users_requires_head_or_admin(client: AsyncClient):
    tokens = await _register_and_login(client, "student_u@test.ru", "student")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.get("/api/v1/users", headers=headers)
    assert resp.status_code == 403


async def test_admin_can_list_users(client: AsyncClient):
    tokens = await _register_and_login(client, "admin_u@test.ru", "admin")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.get("/api/v1/users", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_get_own_profile(client: AsyncClient):
    tokens = await _register_and_login(client, "profile@test.ru", "teacher")
    user_id = tokens.get("access_token")  # we need actual user id
    # Login response doesn't return user, so get from list
    admin_tokens = await _register_and_login(client, "adm2@test.ru", "admin")
    headers_admin = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    users = (await client.get("/api/v1/users", headers=headers_admin)).json()
    user = next((u for u in users if u["email"] == "profile@test.ru"), None)
    assert user is not None

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.get(f"/api/v1/users/{user['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "profile@test.ru"


async def test_admin_can_change_role(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "full_name": "Student2", "email": "s2@test.ru", "password": "pass", "role": "student",
    })
    admin_tokens = await _register_and_login(client, "adm3@test.ru", "admin")
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
