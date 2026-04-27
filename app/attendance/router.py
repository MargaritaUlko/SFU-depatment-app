from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.attendance.schemas import AttendanceCreate, AttendanceOut
from app.attendance.service import create_attendance, get_attendance, list_attendance
from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.users.model import Role

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
async def create_attendance_endpoint(
    data: AttendanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(Role.headman, Role.teacher)),
):
    return await create_attendance(db, data, current_user)


@router.get("", response_model=List[AttendanceOut])
async def list_attendance_endpoint(
    group_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await list_attendance(db, group_id=group_id, skip=skip, limit=limit)


@router.get("/{report_id}", response_model=AttendanceOut)
async def get_attendance_endpoint(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    report = await get_attendance(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Отчёт не найден"
        )
    return report


@router.patch("/{report_id}", response_model=AttendanceOut)
async def update_attendance_endpoint(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    pass


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attendance_endpoint(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    pass
