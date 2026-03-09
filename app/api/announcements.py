from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.announcement import AnnouncementStatus
from app.schemas.announcement import AnnouncementCreate, AnnouncementUpdate, AnnouncementOut
from app.services import announcement_service
from app.api.auth import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/announcements", tags=["announcements"])


def require_roles(*roles: UserRole):
    async def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        return current_user
    return checker


@router.post("/", response_model=AnnouncementOut, status_code=201)
async def create(
    data: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin, UserRole.teacher)),
):
    return await announcement_service.create_announcement(db, data, current_user.id)


@router.get("/", response_model=List[AnnouncementOut])
async def list_announcements(
    status: Optional[AnnouncementStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = current_user.group_name if current_user.role in (UserRole.student, UserRole.starosta) else None
    return await announcement_service.get_announcements(db, group_name=group, status=status, skip=skip, limit=limit)


@router.patch("/{ann_id}", response_model=AnnouncementOut)
async def update(
    ann_id: int,
    data: AnnouncementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin, UserRole.teacher)),
):
    try:
        ann = await announcement_service.update_announcement(
            db, ann_id, data, current_user.id, is_admin=(current_user.role == UserRole.admin)
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    if not ann:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    return ann


@router.delete("/{ann_id}", status_code=204)
async def delete(
    ann_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin, UserRole.teacher)),
):
    try:
        ok = await announcement_service.delete_announcement(
            db, ann_id, current_user.id, is_admin=(current_user.role == UserRole.admin)
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    if not ok:
        raise HTTPException(status_code=404, detail="Объявление не найдено")


@router.post("/{ann_id}/attachments", status_code=201)
async def upload_attachment(
    ann_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin, UserRole.teacher)),
):
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    content = await file.read()

    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"Файл превышает {settings.MAX_FILE_SIZE_MB} МБ")

    attachment = await announcement_service.save_attachment(
        db, ann_id, content, file.filename, file.content_type
    )
    return {"id": attachment.id, "original_name": attachment.original_name, "size_bytes": attachment.size_bytes}