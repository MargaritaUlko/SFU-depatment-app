"""
Фикстуры для тестов.

Используется aiosqlite (SQLite async) вместо PostgreSQL для изоляции.
"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
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


async def create_user_with_role(
    db: AsyncSession, email: str, role: Role, password: str = "pass"
) -> User:
    """Создаёт пользователя с заданной ролью напрямую через DB (обходит register endpoint)."""
    user = User(
        email=email,
        name="Test User",
        hashed_password=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
