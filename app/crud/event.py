import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.models.event import Event, EventLink
from app.schemas.event import EventCreate, EventUpdate


async def get_events(
    db: AsyncSession,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
) -> List[Event]:
    q = select(Event).options(selectinload(Event.links))
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
    result = await db.execute(
        select(Event).where(Event.id == event_id).options(selectinload(Event.links))
    )
    return result.scalar_one_or_none()


async def create_event(db: AsyncSession, data: EventCreate, creator_id: uuid.UUID) -> Event:
    links_data = data.links
    event_dict = data.model_dump(exclude={"links"})
    event = Event(**event_dict, creator_id=creator_id)
    db.add(event)
    await db.flush()  # get event.id

    for lnk in links_data:
        db.add(EventLink(event_id=event.id, **lnk.model_dump()))

    await db.commit()
    await db.refresh(event)
    # reload links
    result = await db.execute(
        select(Event).where(Event.id == event.id).options(selectinload(Event.links))
    )
    return result.scalar_one()


async def update_event(db: AsyncSession, event: Event, data: EventUpdate) -> Event:
    update_dict = data.model_dump(exclude_none=True, exclude={"links"})
    for key, val in update_dict.items():
        setattr(event, key, val)

    if data.links is not None:
        # Replace all links
        for lnk in list(event.links):
            await db.delete(lnk)
        await db.flush()
        for lnk in data.links:
            db.add(EventLink(event_id=event.id, **lnk.model_dump()))

    await db.commit()
    result = await db.execute(
        select(Event).where(Event.id == event.id).options(selectinload(Event.links))
    )
    return result.scalar_one()


async def delete_event(db: AsyncSession, event: Event) -> None:
    await db.delete(event)
    await db.commit()


async def set_event_image(db: AsyncSession, event: Event, image_url: str) -> Event:
    event.image_url = image_url
    await db.commit()
    await db.refresh(event)
    return event
