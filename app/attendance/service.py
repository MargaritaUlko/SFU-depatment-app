from datetime import datetime
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.attendance.crud import (
    create_attendance,
    create_token,
    get_active_token as _get_active_token,
    get_by_lesson,
    get_by_student,
    get_token_by_value,
)
from app.attendance.model import Attendance, AttendanceToken


async def generate_token(db: AsyncSession, lesson_id: int, expires_minutes: int) -> AttendanceToken:
    return await create_token(db, lesson_id, expires_minutes)


async def get_active_token(db: AsyncSession, lesson_id: int) -> AttendanceToken:
    token = await _get_active_token(db, lesson_id)
    if not token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Активный токен не найден")
    if token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Токен истёк")
    return token


async def scan_qr(db: AsyncSession, token_str: str, student_id: int) -> Attendance:
    token = await get_token_by_value(db, token_str)

    if not token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Токен не найден")
    if not token.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Токен неактивен")
    if token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Токен истёк")

    try:
        return await create_attendance(db, token.lesson_id, student_id, marked_via="qr")
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Посещение уже отмечено")


async def mark_manually(db: AsyncSession, lesson_id: int, student_id: int) -> Attendance:
    try:
        return await create_attendance(db, lesson_id, student_id, marked_via="manual")
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Посещение уже отмечено")


async def lesson_attendance(db: AsyncSession, lesson_id: int) -> List[Attendance]:
    return await get_by_lesson(db, lesson_id)


async def student_attendance(db: AsyncSession, student_id: int) -> List[Attendance]:
    return await get_by_student(db, student_id)
