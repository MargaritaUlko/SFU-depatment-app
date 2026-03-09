import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from app.db.session import get_db
from app.models.user import Role
from app.crud.group import get_group
from app.schemas.schedule import ScheduleResponse
from app.services.schedule_parser import fetch_group_schedule, fetch_teacher_schedule, clear_schedule_cache
from app.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.get("/group/{group_id}", response_model=ScheduleResponse)
async def schedule_by_group(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    group = await get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Группа не найдена")

    try:
        result = await fetch_group_schedule(group.sfu_timetable_name)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ошибка при обращении к сайту СФУ: {exc}",
        )
    return result


@router.get("/teacher", response_model=ScheduleResponse)
async def schedule_by_teacher(
    name: str = Query(..., description="ФИО преподавателя, напр. «Кнауб Л. В.»"),
    _=Depends(get_current_user),
):
    try:
        result = await fetch_teacher_schedule(name)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ошибка при обращении к сайту СФУ: {exc}",
        )
    return result


@router.post("/cache/clear")
async def clear_cache(
    _=Depends(require_roles(Role.admin)),
):
    count = clear_schedule_cache()
    return {"cleared": count}
