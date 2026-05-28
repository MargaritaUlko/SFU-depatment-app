import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_group, create_user_with_role, login, make_headers
from app.users.model import Role

pytestmark = pytest.mark.asyncio


async def test_register_success(client: AsyncClient, db: AsyncSession):
    """Студент регистрируется с корректными данными."""
    group = await create_group(db, "КИ25-02")
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Иван",
            "surname": "Иванов",
            "email": "ivan_reg@test.ru",
            "password": "secret123",
            "group_id": group.id,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "ivan_reg@test.ru"
    assert data["role"] == "student"
    assert "id" in data


async def test_register_duplicate_email(client: AsyncClient, db: AsyncSession):
    """Повторная регистрация с тем же email возвращает 400."""
    group = await create_group(db, "КИ25-03")
    payload = {
        "name": "А",
        "surname": "Б",
        "email": "dup@test.ru",
        "password": "pass",
        "group_id": group.id,
    }
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 400


async def test_login_success(client: AsyncClient, db: AsyncSession):
    """Успешный вход возвращает access и refresh токены."""
    await create_user_with_role(db, "login@test.ru", Role.teacher)
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "login@test.ru", "password": "pass"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client: AsyncClient, db: AsyncSession):
    """Неверный пароль возвращает 401."""
    await create_user_with_role(db, "bad@test.ru", Role.student)
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "bad@test.ru", "password": "wrong"},
    )
    assert resp.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient, db: AsyncSession):
    """Вход несуществующего пользователя возвращает 401."""
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@test.ru", "password": "pass"},
    )
    assert resp.status_code == 401


async def test_refresh_token(client: AsyncClient, db: AsyncSession):
    """Refresh-токен обновляет пару access/refresh токенов."""
    await create_user_with_role(db, "ref@test.ru", Role.student)
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "ref@test.ru", "password": "pass"},
    )
    refresh_token = login_resp.json()["refresh_token"]
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_refresh_revoked_after_use(client: AsyncClient, db: AsyncSession):
    """После использования refresh-токен отзывается и не принимается повторно."""
    await create_user_with_role(db, "ref2@test.ru", Role.student)
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "ref2@test.ru", "password": "pass"},
    )
    rt = login_resp.json()["refresh_token"]
    await client.post("/api/v1/auth/refresh", json={"refresh_token": rt})
    # Повторный вызов со старым токеном должен вернуть 401
    resp2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": rt})
    assert resp2.status_code == 401


async def test_logout_revokes_refresh_token(client: AsyncClient, db: AsyncSession):
    """После logout refresh-токен становится недействительным."""
    await create_user_with_role(db, "out@test.ru", Role.student)
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "out@test.ru", "password": "pass"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    resp = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert resp.status_code == 204

    resp2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp2.status_code == 401


async def test_get_me(client: AsyncClient, db: AsyncSession):
    """GET /auth/me возвращает профиль авторизованного пользователя."""
    headers = await make_headers(client, db, "me@test.ru", Role.teacher)
    resp = await client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@test.ru"
