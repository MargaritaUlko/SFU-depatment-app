import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_user_with_role, make_headers
from app.users.model import Role

pytestmark = pytest.mark.asyncio


async def test_get_users_requires_auth(client: AsyncClient, db: AsyncSession):
    """Без токена GET /users возвращает 401 или 403 (FastAPI OAuth2)."""
    resp = await client.get("/api/v1/users")
    assert resp.status_code in (401, 403)


async def test_admin_can_list_users(client: AsyncClient, db: AsyncSession):
    """Администратор получает список пользователей."""
    headers = await make_headers(client, db, "admin_u@test.ru", Role.admin)
    resp = await client.get("/api/v1/users", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_user_appears_in_list(client: AsyncClient, db: AsyncSession):
    """Созданный пользователь присутствует в списке пользователей."""
    user = await create_user_with_role(db, "profile@test.ru", Role.teacher)
    headers = await make_headers(client, db, "adm2@test.ru", Role.admin)
    resp = await client.get("/api/v1/users", headers=headers)
    assert resp.status_code == 200
    ids = [u["id"] for u in resp.json()]
    assert user.id in ids


async def test_update_own_profile(client: AsyncClient, db: AsyncSession):
    """Администратор может обновить имя пользователя через PUT /users/{id}."""
    user = await create_user_with_role(db, "upd@test.ru", Role.teacher)
    headers = await make_headers(client, db, "upd_adm@test.ru", Role.admin)
    resp = await client.put(
        f"/api/v1/users/{user.id}",
        json={"name": "НовоеИмя", "surname": "НоваяФамилия"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "НовоеИмя"


async def test_list_teachers(client: AsyncClient, db: AsyncSession):
    """Список преподавателей доступен авторизованным пользователям."""
    await create_user_with_role(db, "tchr@test.ru", Role.teacher)
    headers = await make_headers(client, db, "tchr_adm@test.ru", Role.admin)
    resp = await client.get("/api/v1/users/teachers", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_search_users_by_surname(client: AsyncClient, db: AsyncSession):
    """Поиск пользователей по фамилии возвращает совпадения."""
    await create_user_with_role(db, "ivanov@test.ru", Role.student, surname="Иванов")
    headers = await make_headers(client, db, "srch_adm@test.ru", Role.admin)
    resp = await client.get("/api/v1/users/search?surname=Иванов", headers=headers)
    assert resp.status_code == 200
    assert any(u["surname"] == "Иванов" for u in resp.json())


async def test_admin_can_delete_user(client: AsyncClient, db: AsyncSession):
    """Администратор может удалить пользователя."""
    user = await create_user_with_role(db, "del@test.ru", Role.student)
    headers = await make_headers(client, db, "del_adm@test.ru", Role.admin)
    resp = await client.delete(f"/api/v1/users/{user.id}", headers=headers)
    assert resp.status_code == 200
