import os
import uuid
from typing import List, Optional

import aiofiles
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.announcements.crud import (
    archive_announcement_,
    create_announcement_,
    delete_announcement_,
    get_announcement_,
    get_announcements_,
    restore_announcement_,
    update_announcement_,
)
from app.announcements.model import Announcement, AnnouncementStatus, Attachment
from app.announcements.schemas import (
    AnnouncementCreate,
    AnnouncementFilters,
    AnnouncementUpdate,
)
from app.core.config import settings
from app.users.crud import get_groups_by_teacher
from app.users.model import Role, StudentProfile, TeacherProfile, User


async def get_announcements(
    db: AsyncSession, filters: AnnouncementFilters, current_user: User
) -> List[Announcement]:
    if current_user.role in (Role.student, Role.headman):
        profile = current_user.student_profiles
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
        data.target_group_ids = [user.student_profile.group_id]
    elif user.role == Role.teacher:
        teacher_groups_ids = await get_groups_by_teacher(db, user.id)
        if data.target_group_ids:
            data.target_group_ids = [
                gid for gid in data.target_group_ids if gid in teacher_groups_ids
            ]
    return await create_announcement_(db, data, user.id)


async def get_announcement(db: AsyncSession, ann_id: int) -> Optional[Announcement]:
    result = await get_announcement_(db, ann_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    return result


async def update_announcement(
    db: AsyncSession,
    ann: Announcement,
    data: AnnouncementUpdate,
    current_user: User,
) -> Announcement:
    if current_user.role == Role.dean:
        pass  # может редактировать любой анонс
    elif current_user.role == Role.deputy_head:
        author_profile = ann.author.teacher_profile if ann.author else None
        my_profile = current_user.teacher_profile
        if (
            author_profile is None
            or my_profile is None
            or author_profile.department != my_profile.department
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Можно редактировать только объявления своей кафедры",
            )
    else:
        # headman и прочие — только своё
        if ann.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Можно редактировать только свои объявления",
            )

    return await update_announcement_(db, ann, data)


async def archive_announcement(
    db: AsyncSession,
    ann_id: int,
    current_user: User,
) -> Announcement:
    ann = await get_announcement(ann_id)
    if ann is None:
        return None
    await check_can_archive(ann, current_user)
    return await archive_announcement_(db, ann_id)


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


async def restore_announcement(
    db: AsyncSession,
    ann_id: int,
    current_user: User,
) -> Announcement:
    ann = await get_announcement(db, ann_id)
    if ann.status != AnnouncementStatus.archived:
        raise HTTPException(status_code=400, detail="Объявление не архивировано")
    return await restore_announcement_(db, ann_id)


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
