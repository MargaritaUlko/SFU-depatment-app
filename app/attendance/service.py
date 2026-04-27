from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.attendance.crud import create_attendance_, get_attendance_, list_attendance_
from app.attendance.model import AttendanceReport
from app.attendance.schemas import AttendanceCreate
from app.users.model import User


async def create_attendance(
    db: AsyncSession,
    data: AttendanceCreate,
    current_user: User,
) -> AttendanceReport:
    return await create_attendance_(db, data, user_id=current_user.id)


async def get_attendance(
    db: AsyncSession, report_id: UUID
) -> Optional[AttendanceReport]:
    return await get_attendance_(db, report_id)


async def list_attendance(
    db: AsyncSession,
    group_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[AttendanceReport]:
    return await list_attendance_(db, group_id=group_id, skip=skip, limit=limit)
