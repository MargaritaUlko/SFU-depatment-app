"""Тесты модуля документов."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import make_headers
from app.users.model import Role

pytestmark = pytest.mark.asyncio

_FILE_CONTENT = b"test document content"
_FILE = ("doc.txt", _FILE_CONTENT, "text/plain")


async def test_teacher_uploads_document(client: AsyncClient, db: AsyncSession):
    """Преподаватель загружает документ с видимостью для студентов."""
    headers = await make_headers(client, db, "t_doc@test.ru", Role.teacher)
    resp = await client.post(
        "/api/v1/documents",
        data={"title": "Лекция 1", "category": "Учебные", "visibility": "student"},
        files={"file": _FILE},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Лекция 1"
    assert "role:student" in data["visibility"]


async def test_student_cannot_upload_document(client: AsyncClient, db: AsyncSession):
    """Студент не может загружать документы."""
    headers = await make_headers(client, db, "st_doc@test.ru", Role.student)
    resp = await client.post(
        "/api/v1/documents",
        data={"title": "X", "category": "Y", "visibility": "student"},
        files={"file": _FILE},
        headers=headers,
    )
    assert resp.status_code == 403


async def test_teacher_lists_documents(client: AsyncClient, db: AsyncSession):
    """Преподаватель получает список доступных документов."""
    headers = await make_headers(client, db, "t_doc2@test.ru", Role.teacher)
    await client.post(
        "/api/v1/documents",
        data={"title": "Лекция 2", "category": "Учебные", "visibility": "teacher"},
        files={"file": _FILE},
        headers=headers,
    )
    resp = await client.get("/api/v1/documents", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_admin_only_document_hidden_from_student(client: AsyncClient, db: AsyncSession):
    """Документ с visibility=admin не виден студенту."""
    teacher_h = await make_headers(client, db, "t_doc3@test.ru", Role.teacher)
    student_h = await make_headers(client, db, "st_doc2@test.ru", Role.student)

    create_resp = await client.post(
        "/api/v1/documents",
        data={"title": "Секрет", "category": "Служебные", "visibility": "admin"},
        files={"file": _FILE},
        headers=teacher_h,
    )
    doc_id = create_resp.json()["id"]

    # Студент не должен видеть документ по ID
    resp = await client.get(f"/api/v1/documents/{doc_id}", headers=student_h)
    assert resp.status_code == 404


async def test_get_nonexistent_document(client: AsyncClient, db: AsyncSession):
    """Запрос несуществующего документа возвращает 404."""
    headers = await make_headers(client, db, "t_doc4@test.ru", Role.teacher)
    resp = await client.get("/api/v1/documents/99999", headers=headers)
    assert resp.status_code == 404
