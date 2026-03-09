import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin

from app.core.config import settings
from app.db.session import engine
from app.admin.auth import AdminAuth
from app.admin.views import (
    UserAdmin,
    RefreshTokenAdmin,
    StreamAdmin,
    GroupAdmin,
    MessageAdmin,
    EventAdmin,
    EventLinkAdmin,
    DocumentAdmin,
)
from app.routers import auth, users, groups, streams, messages, events, documents, schedule, telegram


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

# ── Admin panel (/admin) ──────────────────────────────────────────────────────
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
admin.add_view(EventLinkAdmin)
admin.add_view(DocumentAdmin)
# ─────────────────────────────────────────────────────────────────────────────

# Раздача загружённых файлов
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

PREFIX = "/api/v1"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(users.router, prefix=PREFIX)
app.include_router(groups.router, prefix=PREFIX)
app.include_router(streams.router, prefix=PREFIX)
app.include_router(messages.router, prefix=PREFIX)
app.include_router(telegram.router, prefix=PREFIX)
app.include_router(events.router, prefix=PREFIX)
app.include_router(documents.router, prefix=PREFIX)
app.include_router(schedule.router, prefix=PREFIX)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
