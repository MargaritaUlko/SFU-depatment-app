import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.stream import Stream
from app.schemas.stream import StreamCreate


async def get_streams(db: AsyncSession) -> List[Stream]:
    result = await db.execute(select(Stream))
    return list(result.scalars().all())


async def get_stream(db: AsyncSession, stream_id: uuid.UUID) -> Optional[Stream]:
    result = await db.execute(select(Stream).where(Stream.id == stream_id))
    return result.scalar_one_or_none()


async def create_stream(db: AsyncSession, data: StreamCreate) -> Stream:
    stream = Stream(**data.model_dump())
    db.add(stream)
    await db.commit()
    await db.refresh(stream)
    return stream
