# app/api/v1/router.py
from fastapi import APIRouter
from app.api import auth, announcements, attendance, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(announcements.router)
api_router.include_router(attendance.router)
api_router.include_router(users.router)