import json
import os
import uuid
import aiofiles
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models.announcement import Announcement, Attachment, AnnouncementStatus
from app.models.user import User, UserRole
from app.schemas.announcement import AnnouncementCreate, AnnouncementUpdate
from app.integrations.max_bot import max_bot
from app.core.config import settings


async def create_announcement(
    db: AsyncSession,
    data: AnnouncementCreate,
    author_id: int,
) -> Announcement:
    status = AnnouncementStatus.draft
    if data.publish_at and data.publish_at > datetime.now(timezone.utc):
        status = AnnouncementStatus.scheduled
    elif not data.publish_at:
        status = AnnouncementStatus.published

    ann = Announcement(
        title=data.title,
        content=data.content,
        author_id=author_id,
        publish_at=data.publish_at,
        target_group=data.target_group,
        status=status,
    )
    db.add(ann)
    await db.commit()
    await db.refresh(ann, ["attachments"])

    # Если публикуем сразу — шлём уведомления в Max
    if status == AnnouncementStatus.published:
        await notify_users_about_announcement(db, ann)

    return ann


async def get_announcements(
    db: AsyncSession,
    group_name: Optional[str] = None,
    status: Optional[AnnouncementStatus] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[Announcement]:
    query = select(Announcement).options(selectinload(Announcement.attachments))

    filters = []
    if status:
        filters.append(Announcement.status == status)
    if group_name:
        filters.append(
            (Announcement.target_group == group_name) | (Announcement.target_group == None)
        )

    if filters:
        query = query.where(and_(*filters))

    query = query.order_by(Announcement.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def update_announcement(
    db: AsyncSession,
    ann_id: int,
    data: AnnouncementUpdate,
    current_user_id: int,
    is_admin: bool = False,
) -> Optional[Announcement]:
    result = await db.execute(
        select(Announcement)
        .options(selectinload(Announcement.attachments))
        .where(Announcement.id == ann_id)
    )
    ann = result.scalar_one_or_none()
    if not ann:
        return None
    if not is_admin and ann.author_id != current_user_id:
        raise PermissionError("Нет прав для редактирования")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(ann, field, value)

    # Если статус меняется на published — отправить уведомления
    if data.status == AnnouncementStatus.published and not ann.notified_via_max:
        await notify_users_about_announcement(db, ann)

    await db.commit()
    await db.refresh(ann)
    return ann


async def delete_announcement(
    db: AsyncSession, ann_id: int, current_user_id: int, is_admin: bool = False
) -> bool:
    result = await db.execute(select(Announcement).where(Announcement.id == ann_id))
    ann = result.scalar_one_or_none()
    if not ann:
        return False
    if not is_admin and ann.author_id != current_user_id:
        raise PermissionError("Нет прав для удаления")
    await db.delete(ann)
    await db.commit()
    return True


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


async def notify_users_about_announcement(db: AsyncSession, ann: Announcement):
    """Отправить уведомления в Max всем пользователям (или группе)."""
    query = select(User).where(User.max_user_id != None, User.is_active == True)
    if ann.target_group:
        query = query.where(User.group_name == ann.target_group)

    result = await db.execute(query)
    users = result.scalars().all()

    sent_any = False
    for user in users:
        ok = await max_bot.send_announcement_notification(
            user_max_id=user.max_user_id,
            announcement_title=ann.title,
            announcement_id=ann.id,
            target_group=ann.target_group,
        )
        if ok:
            sent_any = True

    if sent_any:
        ann.notified_via_max = True
        await db.commit()