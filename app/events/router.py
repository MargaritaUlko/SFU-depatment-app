import os
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.file_storage import save_upload_file
from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.events.crud import (
    create_event,
    delete_event,
    get_event,
    get_events,
    set_event_image,
    update_event,
)
from app.events.schemas import EventCreate, EventRead, EventUpdate
from app.users.model import Role

router = APIRouter(prefix="/events", tags=["events"])

_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


@router.get("", response_model=List[EventRead])
async def list_events(
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await get_events(db, from_dt=from_dt, to_dt=to_dt)


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event_endpoint(
    title: str = Form(...),
    starts_at: datetime = Form(...),
    ends_at: datetime = Form(...),
    annotation: Optional[str] = Form(None),
    room_id: Optional[int] = Form(None),
    announcement_id: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(Role.teacher, Role.deputy_head, Role.headman, Role.dean, Role.admin)),
):
    if image and image.content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неподдерживаемый тип файла: {image.content_type}",
        )
    data = EventCreate(
        title=title,
        annotation=annotation,
        starts_at=starts_at,
        ends_at=ends_at,
        room_id=room_id,
        announcement_id=announcement_id,
    )
    event = await create_event(db, data, current_user.id)
    if image:
        directory = os.path.join(settings.UPLOAD_DIR, "events", str(event.id))
        file_path, _ = await save_upload_file(image, directory)
        event = await set_event_image(db, event, "/" + file_path.replace("\\", "/"))
    return event


@router.get("/{event_id}", response_model=EventRead)
async def get_event_endpoint(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    event = await get_event(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Событие не найдено"
        )
    return event


@router.put("/{event_id}", response_model=EventRead)
async def update_event_endpoint(
    event_id: int,
    data: EventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(Role.teacher, Role.deputy_head, Role.headman, Role.dean, Role.admin)),
):
    event = await get_event(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Событие не найдено"
        )
    if event.creator_id != current_user.id and current_user.role not in (
        Role.deputy_head,
        Role.dean,
        Role.admin,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
        )
    return await update_event(db, event, data)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_endpoint(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(Role.teacher, Role.deputy_head, Role.headman, Role.dean, Role.admin)),
):
    event = await get_event(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Событие не найдено"
        )
    if event.creator_id != current_user.id and current_user.role not in (
        Role.deputy_head,
        Role.dean,
        Role.admin,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
        )
    await delete_event(db, event)


@router.post("/{event_id}/image", response_model=EventRead)
async def upload_event_image(
    event_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(Role.teacher, Role.deputy_head, Role.headman, Role.dean, Role.admin)),
):
    event = await get_event(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Событие не найдено"
        )
    if event.creator_id != current_user.id and current_user.role not in (
        Role.deputy_head,
        Role.dean,
        Role.admin,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
        )
    if file.content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неподдерживаемый тип файла: {file.content_type}",
        )

    directory = os.path.join(settings.UPLOAD_DIR, "events", str(event_id))
    file_path, _ = await save_upload_file(file, directory)
    image_url = "/" + file_path.replace("\\", "/")
    return await set_event_image(db, event, image_url)
