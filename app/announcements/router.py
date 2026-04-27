from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.announcements.model import AnnouncementStatus
from app.announcements.schemas import (
    AnnouncementCreate,
    AnnouncementFilters,
    AnnouncementOut,
    AnnouncementUpdate,
)
from app.announcements.service import (
    archive_announcement,
    create_announcement,
    delete_announcement,
    get_announcement,
    get_announcements,
    # update_announcement,
)
from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.users.model import Role

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.get("", response_model=List[AnnouncementOut])
async def list_announcements(
    group_name: Optional[str] = None,
    status: Optional[AnnouncementStatus] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    filters = AnnouncementFilters(
        status=status,
        skip=skip,
        limit=limit,
    )
    return await get_announcements(db, filters, current_user)


@router.post("", response_model=AnnouncementOut, status_code=status.HTTP_201_CREATED)
async def create_announcement_endpoint(
    data: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(Role.teacher, Role.headman, Role.admin)),
):
    return await create_announcement(db, data, current_user)


@router.get("/{ann_id}", response_model=AnnouncementOut)
async def get_announcement_endpoint(
    ann_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ann = await get_announcement(db, ann_id)
    if not ann:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Объявление не найдено"
        )
    return ann


@router.patch("/{ann_id}", response_model=AnnouncementOut)
async def update_announcement_endpoint(
    ann_id: int,
    data: AnnouncementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(Role.headman, Role.deputy_head, Role.dean)),
):
    ann = await update_announcement(db, ann_id, current_user)
    if not ann:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Объявление не найдено"
        )
    return await update_announcement(db, ann, data, current_user)


@router.patch("/{ann_id}", response_model=AnnouncementOut)
async def archive_announcement_endpoint(
    ann_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(Role.headman, Role.deputy_head, Role.dean)),
):
    ann = await get_announcement(db, ann_id, current_user)
    if not ann:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Объявление не найдено"
        )
    return await archive_announcement(db, ann_id, current_user)


@router.delete("/{ann_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement_endpoint(
    ann_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ann = await get_announcement(db, ann_id)
    if not ann:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Объявление не найдено"
        )
    await delete_announcement(db, ann, current_user)
