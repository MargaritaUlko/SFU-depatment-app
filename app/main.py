import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin

from app.admin.auth import AdminAuth
from app.admin.views import (
    DocumentAdmin,
    EventAdmin,
    GroupAdmin,
    MessageAdmin,
    RefreshTokenAdmin,
    StreamAdmin,
    UserAdmin,
)
from app.announcements.router import router as announcements_router
from app.attendance.router import router as attendance_router
from app.auth.router import router as auth_router
from app.core.config import settings
from app.db.session import engine
from app.documents.router import router as documents_router
from app.events.router import router as events_router
from app.groups.router import router as groups_router
from app.messages.router import router as messages_router
from app.streams.router import router as streams_router
from app.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "events"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "documents"), exist_ok=True)
    yield


app = FastAPI(
    title="Department Portal API",
    description=(
        "REST API информационного портала кафедры.\n\n"
        "**Авторизация:** нажмите кнопку **Authorize**, вставьте `access_token` "
        "из ответа `POST /auth/login`."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={"persistAuthorization": True},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

admin = Admin(
    app,
    engine,
    authentication_backend=AdminAuth(secret_key=settings.SECRET_KEY),
    base_url="/admin",
    title="Department Admin",
    logo_url="https://sfu-kras.ru/img/logo.png",
)

admin.add_view(UserAdmin)
admin.add_view(RefreshTokenAdmin)
admin.add_view(StreamAdmin)
admin.add_view(GroupAdmin)
admin.add_view(MessageAdmin)
admin.add_view(EventAdmin)
admin.add_view(DocumentAdmin)

app.mount(
    "/uploads",
    StaticFiles(directory=settings.UPLOAD_DIR, check_dir=False),
    name="uploads",
)

PREFIX = "/api/v1"
app.include_router(auth_router, prefix=PREFIX)
app.include_router(users_router, prefix=PREFIX)
app.include_router(groups_router, prefix=PREFIX)
app.include_router(streams_router, prefix=PREFIX)
app.include_router(messages_router, prefix=PREFIX)
app.include_router(events_router, prefix=PREFIX)
app.include_router(documents_router, prefix=PREFIX)
app.include_router(announcements_router, prefix=PREFIX)
app.include_router(attendance_router, prefix=PREFIX)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
