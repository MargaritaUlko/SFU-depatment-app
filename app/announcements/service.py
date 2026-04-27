import os
import uuid
from typing import List, Optional

import aiofiles
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.announcements.crud import (
    archive_announcement_,
    create_announcement_,
    delete_announcement_,
    get_announcement_,
    get_announcements_,
)
from app.announcements.model import Announcement, AnnouncementStatus, Attachment
from app.announcements.schemas import (
    AnnouncementCreate,
    AnnouncementFilters,
)
from app.core.config import settings
from app.users.model import Role, User


async def get_announcements(
    db: AsyncSession, filters: AnnouncementFilters, current_user: User
) -> List[Announcement]:
    if current_user.role in (Role.student, Role.headman):
        profile = current_user.student_profile
        filters.group_name = profile.group.name
        filters.flow_name = profile.group.stream.name if profile.group.stream else None
    elif current_user.role in (Role.teacher, Role.deputy_head):
        profile = current_user.teacher_profile
        filters.department = profile.department

    return await get_announcements_(db, filters)


async def create_announcement(
    db: AsyncSession,
    data: AnnouncementCreate,
    user: User,
) -> Announcement:
    if user.role == Role.headman:
        target_group = user.student_profile.group_id
    elif user.role == Role.teacher:
        pass
    return await create_announcement_(db, data, author_id)


async def get_announcement(db: AsyncSession, ann_id: int) -> Optional[Announcement]:
    return await get_announcement_(db, ann_id)


async def archive_announcement(
    db: AsyncSession,
    ann: int,
    current_user: User,
) -> Announcement:
    await check_can_archive(ann, current_user)
    return await archive_announcement_(db, ann)


async def check_can_archive(
    announcement: Announcement,
    current_user: User,
) -> None:

    if announcement.status == AnnouncementStatus.archived:
        raise HTTPException(403, "уже архивировано")

    if current_user.role in (Role.dean, Role.admin):
        return

    if current_user.role == Role.deputy_head:
        # может архивировать любое объявление на своей кафедре
        teacher_profile = current_user.teacher_profile
        author_profile = announcement.author.teacher_profile
        if author_profile and author_profile.department == teacher_profile.department:
            return
        raise HTTPException(403, "объявление не с вашей кафедры")

    # остальные только своё
    if announcement.author_id != current_user.id:
        raise HTTPException(403, "можно архивировать только свои объявления")


async def delete_announcement(
    db: AsyncSession,
    ann: Announcement,
    current_user: User,
) -> None:
    if current_user.role != Role.admin and ann.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
        )
    await delete_announcement_(db, ann)


async def save_attachment(
    db: AsyncSession,
    ann_id: int,
    file_data: bytes,
    original_name: str,
    content_type: str,
) -> Attachment:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(original_name)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(file_data)

    attachment = Attachment(
        announcement_id=ann_id,
        filename=filename,
        original_name=original_name,
        content_type=content_type,
        size_bytes=len(file_data),
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return attachment
