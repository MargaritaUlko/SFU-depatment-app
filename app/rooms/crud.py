from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.rooms.model import Room
from app.rooms.schemas import RoomCreate, RoomUpdate


async def get_rooms(db: AsyncSession) -> List[Room]:
    result = await db.execute(select(Room).order_by(Room.number))
    return list(result.scalars().all())


async def get_room(db: AsyncSession, room_id: int) -> Optional[Room]:
    result = await db.execute(select(Room).where(Room.id == room_id))
    return result.scalar_one_or_none()


async def create_room(db: AsyncSession, data: RoomCreate) -> Room:
    room = Room(**data.model_dump())
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


async def update_room(db: AsyncSession, room: Room, data: RoomUpdate) -> Room:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(room, field, value)
    await db.commit()
    await db.refresh(room)
    return room


async def delete_room(db: AsyncSession, room: Room) -> None:
    await db.delete(room)
    await db.commit()
