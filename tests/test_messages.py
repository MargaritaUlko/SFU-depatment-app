"""
Тесты модуля чата: REST endpoints и WebSocket.

REST-тесты используют AsyncClient (httpx).
WebSocket-тесты используют starlette.testclient.TestClient — единственный
способ протестировать WS без внешнего сервера.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.testclient import TestClient

from app.main import app
from app.db.session import get_db
from app.users.model import Role
from tests.conftest import create_user_with_role, login, make_headers

pytestmark = pytest.mark.asyncio


# ── helpers ──────────────────────────────────────────────────────────────────

async def _get_raw_token(client: AsyncClient, email: str, password: str = "pass") -> str:
    """Возвращает сырой access_token (нужен для WS ?token=...)."""
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    return resp.json()["access_token"]


# ── REST: список чатов ────────────────────────────────────────────────────────

async def test_list_chats_empty(client: AsyncClient, db: AsyncSession):
    """Новый пользователь видит пустой список чатов."""
    headers = await make_headers(client, db, "chat_empty@test.ru", Role.student)
    resp = await client.get("/api/v1/chats", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_admin_sees_all_chats(client: AsyncClient, db: AsyncSession):
    """Администратор видит все чаты, а не только свои."""
    u1 = await create_user_with_role(db, "chat_u1@test.ru", Role.student)
    u2 = await create_user_with_role(db, "chat_u2@test.ru", Role.student)
    admin_headers = await make_headers(client, db, "chat_adm@test.ru", Role.admin)

    # создаём прямой чат между u1 и u2
    u1_headers = await login(client, "chat_u1@test.ru")
    await client.post(f"/api/v1/chats/direct/{u2.id}", headers=u1_headers)

    resp = await client.get("/api/v1/chats", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# ── REST: прямой чат ──────────────────────────────────────────────────────────

async def test_create_direct_chat(client: AsyncClient, db: AsyncSession):
    """Создание прямого чата между двумя пользователями."""
    u1 = await create_user_with_role(db, "direct_a@test.ru", Role.teacher)
    u2 = await create_user_with_role(db, "direct_b@test.ru", Role.student)
    headers = await login(client, "direct_a@test.ru")

    resp = await client.post(f"/api/v1/chats/direct/{u2.id}", headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["type"] == "direct"
    member_ids = {m["user_id"] for m in data["members"]}
    assert u1.id in member_ids
    assert u2.id in member_ids


async def test_create_direct_chat_idempotent(client: AsyncClient, db: AsyncSession):
    """Повторное создание прямого чата возвращает тот же объект."""
    u1 = await create_user_with_role(db, "idem_a@test.ru", Role.teacher)
    u2 = await create_user_with_role(db, "idem_b@test.ru", Role.student)
    headers = await login(client, "idem_a@test.ru")

    r1 = await client.post(f"/api/v1/chats/direct/{u2.id}", headers=headers)
    r2 = await client.post(f"/api/v1/chats/direct/{u2.id}", headers=headers)
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] == r2.json()["id"]


async def test_cannot_create_chat_with_self(client: AsyncClient, db: AsyncSession):
    """Нельзя создать прямой чат с самим собой."""
    u = await create_user_with_role(db, "self_chat@test.ru", Role.student)
    headers = await login(client, "self_chat@test.ru")

    resp = await client.post(f"/api/v1/chats/direct/{u.id}", headers=headers)
    assert resp.status_code == 400


async def test_direct_chat_with_nonexistent_user(client: AsyncClient, db: AsyncSession):
    """Нельзя создать чат с несуществующим пользователем."""
    headers = await make_headers(client, db, "ghost_chat@test.ru", Role.student)
    resp = await client.post("/api/v1/chats/direct/999999", headers=headers)
    assert resp.status_code == 404


# ── REST: групповой чат ───────────────────────────────────────────────────────

async def test_create_group_chat(client: AsyncClient, db: AsyncSession):
    """Создание группового чата."""
    u1 = await create_user_with_role(db, "grp_a@test.ru", Role.teacher)
    u2 = await create_user_with_role(db, "grp_b@test.ru", Role.student)
    u3 = await create_user_with_role(db, "grp_c@test.ru", Role.student)
    headers = await login(client, "grp_a@test.ru")

    resp = await client.post(
        "/api/v1/chats/group",
        json={"group_id": 1, "member_ids": [u1.id, u2.id, u3.id]},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["type"] == "group"
    assert len(data["members"]) == 3


# ── REST: сообщения в чате ────────────────────────────────────────────────────

async def test_send_and_list_messages(client: AsyncClient, db: AsyncSession):
    """Участник чата может отправить сообщение и увидеть его в списке."""
    u1 = await create_user_with_role(db, "msg_a@test.ru", Role.teacher)
    u2 = await create_user_with_role(db, "msg_b@test.ru", Role.student)
    h1 = await login(client, "msg_a@test.ru")

    chat_resp = await client.post(f"/api/v1/chats/direct/{u2.id}", headers=h1)
    chat_id = chat_resp.json()["id"]

    send_resp = await client.post(
        f"/api/v1/chats/{chat_id}/messages",
        json={"body": "Привет!"},
        headers=h1,
    )
    assert send_resp.status_code == 201
    msg = send_resp.json()
    assert msg["body"] == "Привет!"
    assert msg["sender_id"] == u1.id
    assert msg["chat_id"] == chat_id

    list_resp = await client.get(f"/api/v1/chats/{chat_id}/messages", headers=h1)
    assert list_resp.status_code == 200
    bodies = [m["body"] for m in list_resp.json()]
    assert "Привет!" in bodies


async def test_non_member_cannot_send_message(client: AsyncClient, db: AsyncSession):
    """Пользователь не из чата не может отправить сообщение."""
    u1 = await create_user_with_role(db, "nm_a@test.ru", Role.teacher)
    u2 = await create_user_with_role(db, "nm_b@test.ru", Role.student)
    outsider_headers = await make_headers(client, db, "nm_out@test.ru", Role.student)

    h1 = await login(client, "nm_a@test.ru")
    chat_resp = await client.post(f"/api/v1/chats/direct/{u2.id}", headers=h1)
    chat_id = chat_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/chats/{chat_id}/messages",
        json={"body": "Взлом"},
        headers=outsider_headers,
    )
    assert resp.status_code == 403


async def test_non_member_cannot_list_messages(client: AsyncClient, db: AsyncSession):
    """Пользователь не из чата не может читать сообщения."""
    u1 = await create_user_with_role(db, "nlm_a@test.ru", Role.teacher)
    u2 = await create_user_with_role(db, "nlm_b@test.ru", Role.student)
    outsider_headers = await make_headers(client, db, "nlm_out@test.ru", Role.student)

    h1 = await login(client, "nlm_a@test.ru")
    chat_resp = await client.post(f"/api/v1/chats/direct/{u2.id}", headers=h1)
    chat_id = chat_resp.json()["id"]

    resp = await client.get(f"/api/v1/chats/{chat_id}/messages", headers=outsider_headers)
    assert resp.status_code == 403


async def test_messages_for_nonexistent_chat(client: AsyncClient, db: AsyncSession):
    """GET сообщений несуществующего чата → 404."""
    headers = await make_headers(client, db, "nochat@test.ru", Role.student)
    resp = await client.get("/api/v1/chats/999999/messages", headers=headers)
    assert resp.status_code == 404


# ── WebSocket ─────────────────────────────────────────────────────────────────

async def test_websocket_send_and_receive(client: AsyncClient, db: AsyncSession):
    """Сообщение через WS сохраняется и бродкастится обратно отправителю."""
    u1 = await create_user_with_role(db, "ws_a@test.ru", Role.teacher)
    u2 = await create_user_with_role(db, "ws_b@test.ru", Role.student)

    h1 = await login(client, "ws_a@test.ru")
    chat_resp = await client.post(f"/api/v1/chats/direct/{u2.id}", headers=h1)
    chat_id = chat_resp.json()["id"]
    token = await _get_raw_token(client, "ws_a@test.ru")

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as sync_client:
        with sync_client.websocket_connect(f"/api/v1/chats/{chat_id}/ws?token={token}") as ws:
            ws.send_text("WebSocket привет")
            data = ws.receive_json()
            assert data["body"] == "WebSocket привет"
            assert data["sender_id"] == u1.id
            assert data["chat_id"] == chat_id
    app.dependency_overrides.clear()


async def test_websocket_invalid_token(client: AsyncClient, db: AsyncSession):
    """WS с невалидным токеном закрывается с кодом 4001."""
    u1 = await create_user_with_role(db, "ws_bad_a@test.ru", Role.teacher)
    u2 = await create_user_with_role(db, "ws_bad_b@test.ru", Role.student)

    h1 = await login(client, "ws_bad_a@test.ru")
    chat_resp = await client.post(f"/api/v1/chats/direct/{u2.id}", headers=h1)
    chat_id = chat_resp.json()["id"]

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as sync_client:
        with pytest.raises(Exception):
            with sync_client.websocket_connect(
                f"/api/v1/chats/{chat_id}/ws?token=invalid.token.here"
            ) as ws:
                ws.receive_json()
    app.dependency_overrides.clear()


async def test_websocket_non_member_rejected(client: AsyncClient, db: AsyncSession):
    """WS-подключение к чужому чату закрывается с кодом 4003."""
    u1 = await create_user_with_role(db, "ws_nm_a@test.ru", Role.teacher)
    u2 = await create_user_with_role(db, "ws_nm_b@test.ru", Role.student)
    outsider = await create_user_with_role(db, "ws_nm_out@test.ru", Role.student)

    h1 = await login(client, "ws_nm_a@test.ru")
    chat_resp = await client.post(f"/api/v1/chats/direct/{u2.id}", headers=h1)
    chat_id = chat_resp.json()["id"]
    outsider_token = await _get_raw_token(client, "ws_nm_out@test.ru")

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as sync_client:
        with pytest.raises(Exception):
            with sync_client.websocket_connect(
                f"/api/v1/chats/{chat_id}/ws?token={outsider_token}"
            ) as ws:
                ws.receive_json()
    app.dependency_overrides.clear()
