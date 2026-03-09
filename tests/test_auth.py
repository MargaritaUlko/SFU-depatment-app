import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_register(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "full_name": "Иван Иванов",
        "email": "ivan@test.ru",
        "password": "secret123",
        "role": "student",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "ivan@test.ru"
    assert data["role"] == "student"
    assert "id" in data


async def test_register_duplicate_email(client: AsyncClient):
    payload = {"full_name": "А", "email": "dup@test.ru", "password": "pass", "role": "student"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 400


async def test_login(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "full_name": "Test", "email": "login@test.ru", "password": "pass123", "role": "student",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@test.ru", "password": "pass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "full_name": "T", "email": "bad@test.ru", "password": "correct", "role": "student",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "bad@test.ru", "password": "wrong",
    })
    assert resp.status_code == 401


async def test_refresh(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "full_name": "Ref", "email": "ref@test.ru", "password": "pass", "role": "student",
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "ref@test.ru", "password": "pass",
    })
    refresh_token = login_resp.json()["refresh_token"]
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_logout(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "full_name": "Out", "email": "out@test.ru", "password": "pass", "role": "student",
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "out@test.ru", "password": "pass",
    })
    refresh_token = login_resp.json()["refresh_token"]
    resp = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert resp.status_code == 204

    # После logout refresh_token должен быть недействительным
    resp2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp2.status_code == 401
