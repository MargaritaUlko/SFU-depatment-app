"""
Скрипт создания суперпользователя (role=admin).

Использование:
    python create_superuser.py
    python create_superuser.py --email admin@example.com --password secret --name "Ivan Ivanov"
"""

import argparse
import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.users.model import Role, User


async def create_superuser(name: str, email: str, password: str) -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            print(f"[!] Пользователь с email '{email}' уже существует.")
            await engine.dispose()
            sys.exit(1)

        user = User(
            name=name,
            email=email,
            hashed_password=hash_password(password),
            role=Role.admin,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print("[+] Суперпользователь создан:")
        print(f"    ID:    {user.id}")
        print(f"    Email: {user.email}")
        print(f"    Роль:  {user.role.value}")

    await engine.dispose()


def prompt(label: str, secret: bool = False) -> str:
    import getpass

    return getpass.getpass(f"{label}: ") if secret else input(f"{label}: ")


def main() -> None:
    parser = argparse.ArgumentParser(description="Создать суперпользователя (admin)")
    parser.add_argument("--email", default=None)
    parser.add_argument("--password", default=None)
    parser.add_argument("--name", default=None, dest="name")
    args = parser.parse_args()

    name = args.name or prompt("Имя")
    email = args.email or prompt("Email")
    password = args.password or prompt("Пароль", secret=True)

    if not password:
        print("[!] Пароль не может быть пустым.")
        sys.exit(1)

    asyncio.run(create_superuser(name, email, password))


if __name__ == "__main__":
    main()
