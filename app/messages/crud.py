import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.messages.model import Message
from app.users.model import User, Role
from app.messages.schemas import MessageCreate


async def create_message(db: AsyncSession, data: MessageCreate, sender_id: uuid.UUID) -> Message:
    msg = Message(**data.model_dump(), sender_id=sender_id)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_messages(db: AsyncSession, user: User) -> List[Message]:
    if user.role == Role.admin:
        result = await db.execute(select(Message).order_by(Message.created_at.desc()))
    else:
        result = await db.execute(
            select(Message)
            .where(Message.sender_id == user.id)
            .order_by(Message.created_at.desc())
        )
    return list(result.scalars().all())


async def get_message(db: AsyncSession, message_id: uuid.UUID) -> Optional[Message]:
    result = await db.execute(select(Message).where(Message.id == message_id))
    return result.scalar_one_or_none()
