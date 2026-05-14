from typing import List, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.announcements.model import Announcement, AnnouncementStatus
from app.announcements.schemas import (
    AnnouncementCreate,
    AnnouncementFilters,
    AnnouncementUpdate,
)
from app.groups.model import Group
from app.streams.model import Stream
from app.users.model import User


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
    author_id: int,
) -> Announcement:
    groups, streams = [], []
    if data.target_group_ids:
        result = await db.execute(select(Group).where(Group.id.in_(data.target_group_ids)))
        groups = list(result.scalars().all())
    if data.target_stream_ids:
        result = await db.execute(select(Stream).where(Stream.id.in_(data.target_stream_ids)))
        streams = list(result.scalars().all())

    ann = Announcement(
        title=data.title,
        content=data.content,
        publish_at=data.publish_at,
        target_groups=groups,
        target_streams=streams,
        author_id=author_id,
        status=AnnouncementStatus.draft,
    )
    db.add(ann)
    await db.commit()
    await db.refresh(ann)
    return await get_announcement_(db, ann.id)


async def get_announcement_(db: AsyncSession, ann_id: int) -> Optional[Announcement]:
    result = await db.execute(
        select(Announcement)
        .where(Announcement.id == ann_id)
        .options(
            selectinload(Announcement.attachments),
            selectinload(Announcement.author).selectinload(User.teacher_profile),
        )
    )
    return result.scalar_one_or_none()


async def archive_announcement_(
    db: AsyncSession,
    ann_id: int,
) -> Announcement:
    await db.execute(
        update(Announcement)
        .where(Announcement.id == ann_id)
        .values(status=AnnouncementStatus.archived)
    )
    await db.commit()
    return await get_announcement_(db, ann_id)


async def restore_announcement_(
    db: AsyncSession,
    ann_id: int,
) -> Announcement:
    await db.execute(
        update(Announcement)
        .where(Announcement.id == ann_id)
        .values(status=AnnouncementStatus.published)
    )
    await db.commit()
    return await get_announcement_(db, ann_id)


async def update_announcement_(
    db: AsyncSession,
    ann: Announcement,
    data: AnnouncementUpdate,
) -> Announcement:
    if data.title is not None:
        ann.title = data.title
    if data.content is not None:
        ann.content = data.content
    if data.target_group_ids is not None:
        result = await db.execute(select(Group).where(Group.id.in_(data.target_group_ids)))
        ann.target_groups = list(result.scalars().all())
    if data.target_stream_ids is not None:
        result = await db.execute(select(Stream).where(Stream.id.in_(data.target_stream_ids)))
        ann.target_streams = list(result.scalars().all())
    if data.publish_at is not None:
        ann.publish_at = data.publish_at
    if data.expires_at is not None:
        ann.expires_at = data.expires_at
    await db.commit()
    return await get_announcement_(db, ann.id)


async def delete_announcement_(db: AsyncSession, ann: Announcement) -> None:
    await db.delete(ann)
    await db.commit()
