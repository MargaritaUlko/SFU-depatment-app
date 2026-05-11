import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.events.model import Event
from app.events.schemas import EventCreate, EventUpdate


async def get_events(
    db: AsyncSession,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
) -> List[Event]:
    q = select(Event).options(selectinload(Event.room))
    filters = []
    if from_dt:
        filters.append(Event.starts_at >= from_dt)
    if to_dt:
        filters.append(Event.ends_at <= to_dt)
    if filters:
        q = q.where(and_(*filters))
    q = q.order_by(Event.starts_at)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_event(db: AsyncSession, event_id: uuid.UUID) -> Optional[Event]:
    result = await db.execute(select(Event).options(selectinload(Event.room)).where(Event.id == event_id))
    return result.scalar_one_or_none()


async def _get_event_with_room(db: AsyncSession, event_id: int) -> Event:
    result = await db.execute(
        select(Event).where(Event.id == event_id).options(selectinload(Event.room))
    )
    return result.scalar_one()


async def create_event(
    db: AsyncSession, data: EventCreate, creator_id: uuid.UUID
) -> Event:
    event_dict = data.model_dump(exclude={"links"})
    event = Event(**event_dict, creator_id=creator_id)
    db.add(event)
    await db.commit()
    return await _get_event_with_room(db, event.id)


async def update_event(db: AsyncSession, event: Event, data: EventUpdate) -> Event:
    update_dict = data.model_dump(exclude_none=True, exclude={"links"})
    for key, val in update_dict.items():
        setattr(event, key, val)
    await db.commit()
    return await _get_event_with_room(db, event.id)


async def delete_event(db: AsyncSession, event: Event) -> None:
    await db.delete(event)
    await db.commit()


async def set_event_image(db: AsyncSession, event: Event, image_url: str) -> Event:
    event.image_url = image_url
    await db.commit()
    return await _get_event_with_room(db, event.id)
