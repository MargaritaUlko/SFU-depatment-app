"""
Создание тестовых пользователей для нагрузочного тестирования.

Пишет напрямую в БД (не через API) — работает до старта сервера.
Идемпотентен: пропускает уже существующих пользователей.

Использование:
    python load_tests/create_test_users.py
    python load_tests/create_test_users.py --host http://localhost:8000
"""

import asyncio
import os
import sys

# Позволяет запускать скрипт из корня проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import Role, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password

# ── Описание тестовых пользователей ──────────────────────────────────────────
TEST_USERS = [
    {
        "name": "Load Test Student",
        "email": os.getenv("STUDENT_EMAIL", "student@test.com"),
        "password": os.getenv("STUDENT_PASSWORD", "student123"),
        "role": Role.student,
    },
    {
        "name": "Load Test Teacher",
        "email": os.getenv("TEACHER_EMAIL", "teacher@test.com"),
        "password": os.getenv("TEACHER_PASSWORD", "teacher123"),
        "role": Role.teacher,
    },
    {
        "name": "Load Test Admin",
        "email": os.getenv("ADMIN_EMAIL", "admin@test.com"),
        "password": os.getenv("ADMIN_PASSWORD", "admin123"),
        "role": Role.admin,
    },
]


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        for spec in TEST_USERS:
            result = await db.execute(select(User).where(User.email == spec["email"]))
            existing = result.scalar_one_or_none()

            if existing:
                print(
                    f"[~] Уже существует: {spec['email']} (role={existing.role.value})"
                )
                # Обновляем роль, если она изменилась
                if existing.role != spec["role"]:
                    existing.role = spec["role"]
                    await db.commit()
                    print(f"    Роль обновлена -> {spec['role'].value}")
                continue

            user = User(
                name=spec["name"],
                email=spec["email"],
                hashed_password=hash_password(spec["password"]),
                role=spec["role"],
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"[+] Создан: {user.email}  role={user.role.value}  id={user.id}")

    await engine.dispose()
    print("\nГотово. Запустите нагрузочный тест:")
    print("  locust -f load_tests/locustfile.py --host http://localhost:8000")


if __name__ == "__main__":
    asyncio.run(main())
