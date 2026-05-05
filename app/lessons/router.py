from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.lessons.crud import get_lessons_by_group, get_lessons_by_teacher
from app.lessons.schemas import LessonOut, SyncResult
from app.lessons.service import sync_lessons
from app.users.model import Role

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/group/{group_id}", response_model=List[LessonOut])
async def lessons_by_group(
    group_id: int,
    week: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await get_lessons_by_group(db, group_id, week)


@router.get("/teacher/{teacher_id}", response_model=List[LessonOut])
async def lessons_by_teacher(
    teacher_id: int,
    week: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await get_lessons_by_teacher(db, teacher_id, week)


@router.post("/sync", response_model=SyncResult)
async def sync(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(Role.admin)),
):
    return await sync_lessons(db)
