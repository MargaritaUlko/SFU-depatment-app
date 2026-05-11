from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.streams.model import Stream
from app.streams.schemas import StreamCreate, StreamUpdate


async def get_streams(db: AsyncSession) -> List[Stream]:
    result = await db.execute(select(Stream))
    return list(result.scalars().all())


async def get_stream(db: AsyncSession, stream_id: int) -> Optional[Stream]:
    result = await db.execute(select(Stream).where(Stream.id == stream_id))
    return result.scalar_one_or_none()


async def create_stream(db: AsyncSession, data: StreamCreate) -> Stream:
    stream = Stream(**data.model_dump())
    db.add(stream)
    await db.commit()
    await db.refresh(stream)
    return stream


async def update_stream(db: AsyncSession, stream: Stream, data: StreamUpdate) -> Stream:
    for key, val in data.model_dump(exclude_none=True).items():
        setattr(stream, key, val)
    await db.commit()
    await db.refresh(stream)
    return stream


async def delete_stream(db: AsyncSession, stream: Stream) -> None:
    await db.delete(stream)
    await db.commit()
