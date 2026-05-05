from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.attendance.model import Attendance, AttendanceToken


async def create_token(db: AsyncSession, lesson_id: int, expires_minutes: int) -> AttendanceToken:
    existing = await db.execute(
        select(AttendanceToken).where(
            AttendanceToken.lesson_id == lesson_id,
            AttendanceToken.is_active == True,
        )
    )
    for t in existing.scalars():
        t.is_active = False

    token = AttendanceToken(
        lesson_id=lesson_id,
        token=str(uuid4()),
        expires_at=datetime.utcnow() + timedelta(minutes=expires_minutes),
    )
    db.add(token)
    await db.commit()
    await db.refresh(token)
    return token


async def get_active_token(db: AsyncSession, lesson_id: int) -> Optional[AttendanceToken]:
    result = await db.execute(
        select(AttendanceToken).where(
            AttendanceToken.lesson_id == lesson_id,
            AttendanceToken.is_active == True,
        )
    )
    return result.scalar_one_or_none()


async def get_token_by_value(db: AsyncSession, token: str) -> Optional[AttendanceToken]:
    result = await db.execute(select(AttendanceToken).where(AttendanceToken.token == token))
    return result.scalar_one_or_none()


async def create_attendance(
    db: AsyncSession, lesson_id: int, student_id: int, marked_via: str
) -> Attendance:
    record = Attendance(lesson_id=lesson_id, student_id=student_id, marked_via=marked_via)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_by_lesson(db: AsyncSession, lesson_id: int) -> List[Attendance]:
    result = await db.execute(select(Attendance).where(Attendance.lesson_id == lesson_id))
    return result.scalars().all()


async def get_by_student(db: AsyncSession, student_id: int) -> List[Attendance]:
    result = await db.execute(select(Attendance).where(Attendance.student_id == student_id))
    return result.scalars().all()
