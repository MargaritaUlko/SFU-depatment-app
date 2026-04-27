from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.announcements.model import Announcement, AnnouncementStatus
from app.announcements.schemas import (
    AnnouncementCreate,
    AnnouncementFilters,
    AnnouncementUpdate,
)


async def get_announcements_(
    db: AsyncSession,
    filters: AnnouncementFilters,
) -> List[Announcement]:
    query = (
        select(Announcement)
        .options(selectinload(Announcement.attachments))
        .order_by(Announcement.created_at.desc())
    )

    filters_list = [Announcement.status == AnnouncementStatus.published]

    if filters.group_name:
        filters_list.append(
            (Announcement.target_group == filters.group_name)
            | (Announcement.target_group == None)  # noqa: E711
        )

    if filters.flow_name:
        filters_list.append(
            (Announcement.target_flow == filters.flow_name)
            | (Announcement.target_flow == None)  # noqa: E711
        )

    if filters_list:
        query = query.where(and_(*filters_list))

    query = query.offset(filters.skip).limit(filters.limit)
    result = await db.execute(query)
    return result.scalars().all()


async def create_announcement_(
    db: AsyncSession,
    data: AnnouncementCreate,
    author_id: UUID,
) -> Announcement:
    ann = Announcement(
        title=data.title,
        content=data.content,
        publish_at=data.publish_at,
        target_group=data.target_group,
        author_id=author_id,
        status=AnnouncementStatus.draft,
    )
    db.add(ann)
    await db.commit()
    await db.refresh(ann)
    return ann


async def get_announcement_(db: AsyncSession, ann_id: int) -> Optional[Announcement]:
    result = await db.execute(
        select(Announcement)
        .where(Announcement.id == ann_id)
        .options(selectinload(Announcement.attachments))
    )
    return result.scalar_one_or_none()


async def archive_announcement_(
    db: AsyncSession,
    ann_id: int,
) -> Announcement:
    result = await db.execute(
        update(Announcement)
        .where(Announcement.id == ann_id)
        .values(status="archived")
        .returning(Announcement)
    )
    await db.commit()
    return result.scalar_one()


async def update_announcement_(
    db: AsyncSession,
    ann: Announcement,
    data: AnnouncementUpdate,
) -> Announcement:
    if data.title is not None:
        ann.title = data.title
    if data.content is not None:
        ann.content = data.content
    if data.target_group is not None:
        ann.target_group = data.target_group
    if data.status is not None:
        ann.status = data.status
    await db.commit()
    await db.refresh(ann)
    return ann


async def delete_announcement_(db: AsyncSession, ann: Announcement) -> None:
    await db.delete(ann)
    await db.commit()
