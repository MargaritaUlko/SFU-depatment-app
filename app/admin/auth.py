from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.users.model import User, Role
from app.core.security import verify_password


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = form.get("username", "")
        password = form.get("password", "")

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

        if not user:
            return False
        if not verify_password(password, user.hashed_password):
            return False
        if user.role != Role.admin or not user.is_active:
            return False

        request.session.update({"admin_user_id": str(user.id)})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return "admin_user_id" in request.session
