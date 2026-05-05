import io
from typing import List

import qrcode
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.attendance.schemas import AttendanceOut, AttendanceTokenOut
from app.attendance.service import (
    generate_token,
    get_active_token,
    lesson_attendance,
    mark_manually,
    scan_qr,
    student_attendance,
)
from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.users.model import Role

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/token/{lesson_id}", response_model=AttendanceTokenOut, status_code=status.HTTP_201_CREATED)
async def create_token_endpoint(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(Role.teacher, Role.headman)),
):
    return await generate_token(db, lesson_id, expires_minutes=15)


@router.get("/token/{lesson_id}/qr")
async def get_qr_endpoint(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(Role.teacher, Role.headman)),
):
    token = await get_active_token(db, lesson_id)
    img = qrcode.make(token.token)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@router.post("/scan/{token}", response_model=AttendanceOut)
async def scan_qr_endpoint(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(Role.student, Role.headman)),
):
    return await scan_qr(db, token, current_user.id)


@router.post("/manual/{lesson_id}/{student_id}", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
async def mark_manual_endpoint(
    lesson_id: int,
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(Role.teacher, Role.headman)),
):
    return await mark_manually(db, lesson_id, student_id)


@router.get("/lesson/{lesson_id}", response_model=List[AttendanceOut])
async def get_lesson_attendance_endpoint(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await lesson_attendance(db, lesson_id)


@router.get("/student/{student_id}", response_model=List[AttendanceOut])
async def get_student_attendance_endpoint(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await student_attendance(db, student_id)
