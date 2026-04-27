from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.attendance.model import AttendanceReport
from app.attendance.schemas import AttendanceCreate


async def create_attendance_(
    db: AsyncSession,
    data: AttendanceCreate,
    starosta_id: UUID,
) -> AttendanceReport:
    report = AttendanceReport(
        starosta_id=starosta_id,
        teacher_id=data.teacher_id,
        group_id=data.group_id,
        subject=data.subject,
        lesson_date=data.lesson_date,
        present_student_ids=data.present_student_ids,
        total_students=data.total_students,
        present_count=len(data.present_student_ids),
        notes=data.notes,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def get_attendance_(
    db: AsyncSession, report_id: UUID
) -> Optional[AttendanceReport]:
    result = await db.execute(
        select(AttendanceReport).where(AttendanceReport.id == report_id)
    )
    return result.scalar_one_or_none()


async def list_attendance_(
    db: AsyncSession,
    group_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[AttendanceReport]:
    query = select(AttendanceReport).order_by(AttendanceReport.lesson_date.desc())
    if group_id:
        query = query.where(AttendanceReport.group_id == group_id)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
