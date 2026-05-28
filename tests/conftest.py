"""
Фикстуры для тестов.

Используется aiosqlite (SQLite async) вместо PostgreSQL для изоляции.
ARRAY-тип PostgreSQL заменяется на JSON для совместимости с SQLite.
"""

import sqlalchemy as sa
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ── патч до любого create_all ────────────────────────────────────────────────
# TeacherProfile.positions использует postgresql.ARRAY, которого нет в SQLite.
# Заменяем на JSON — семантика та же, SQLite поддерживает.
from app.users.model import TeacherProfile  # noqa: E402 — после патча
TeacherProfile.__table__.c.positions.type = sa.JSON()
# ─────────────────────────────────────────────────────────────────────────────

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.groups.model import Group
from app.main import app
from app.users.model import Role, User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture()
async def db(engine):
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture()
async def client(db: AsyncSession):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ── helpers ──────────────────────────────────────────────────────────────────

async def create_user_with_role(
    db: AsyncSession,
    email: str,
    role: Role,
    password: str = "pass",
    name: str = "Тест",
    surname: str = "Тестовый",
) -> User:
    """Создаёт пользователя с заданной ролью напрямую через DB."""
    user = User(
        email=email,
        name=name,
        surname=surname,
        hashed_password=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_group(
    db: AsyncSession, name: str = "КИ25-01", year: int = 2025
) -> Group:
    """Создаёт учебную группу напрямую в DB."""
    group = Group(name=name, year=year)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def login(client: AsyncClient, email: str, password: str = "pass") -> dict:
    """Логинит пользователя и возвращает заголовки Authorization."""
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def make_headers(
    client: AsyncClient,
    db: AsyncSession,
    email: str,
    role: Role,
    password: str = "pass",
) -> dict:
    """Создаёт пользователя и возвращает заголовки с его токеном."""
    await create_user_with_role(db, email, role, password)
    return await login(client, email, password)
