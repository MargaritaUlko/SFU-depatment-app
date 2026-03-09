import json
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.attendance import AttendanceReport
from app.schemas.attendance import AttendanceCreate, AttendanceOut
from app.api.auth import get_current_user
from app.integrations.max_bot import max_bot

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/", response_model=AttendanceOut, status_code=201)
async def submit_attendance(
    data: AttendanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.starosta, UserRole.admin):
        raise HTTPException(status_code=403, detail="Только старосты могут отправлять списки")

    # Проверяем что преподаватель существует
    result = await db.execute(select(User).where(User.id == data.teacher_id, User.role == UserRole.teacher))
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")

    report = AttendanceReport(
        starosta_id=current_user.id,
        teacher_id=data.teacher_id,
        subject=data.subject,
        group_name=data.group_name,
        lesson_date=data.lesson_date,
        present_students=json.dumps(data.present_students, ensure_ascii=False),
        total_students=data.total_students,
        present_count=len(data.present_students),
        notes=data.notes,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    # Уведомить преподавателя в Max
    if teacher.max_user_id:
        await max_bot.send_attendance_notification(
            teacher_max_id=teacher.max_user_id,
            starosta_name=current_user.full_name,
            subject=data.subject,
            group_name=data.group_name,
            present_count=report.present_count,
            total_students=data.total_students,
            report_id=report.id,
        )

    return report


@router.get("/", response_model=List[AttendanceOut])
async def get_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.teacher:
        query = select(AttendanceReport).where(AttendanceReport.teacher_id == current_user.id)
    elif current_user.role == UserRole.starosta:
        query = select(AttendanceReport).where(AttendanceReport.starosta_id == current_user.id)
    elif current_user.role == UserRole.admin:
        query = select(AttendanceReport)
    else:
        raise HTTPException(status_code=403, detail="Нет доступа")

    result = await db.execute(query.order_by(AttendanceReport.created_at.desc()))
    return result.scalars().all()


@router.get("/{report_id}", response_model=AttendanceOut)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(AttendanceReport).where(AttendanceReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Отчёт не найден")

    if current_user.role not in (UserRole.admin,):
        if report.teacher_id != current_user.id and report.starosta_id != current_user.id:
            raise HTTPException(status_code=403, detail="Нет доступа")

    return report