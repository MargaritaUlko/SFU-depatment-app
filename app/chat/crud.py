from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.chat.model import Chat, ChatMember, ChatMessage, ChatType


async def get_user_chats(db: AsyncSession, user_id: int) -> List[Chat]:
    result = await db.execute(
        select(Chat)
        .join(ChatMember, Chat.id == ChatMember.chat_id)
        .where(ChatMember.user_id == user_id)
        .options(selectinload(Chat.members))
    )
    return list(result.scalars().all())


async def get_chat(db: AsyncSession, chat_id: int) -> Optional[Chat]:
    result = await db.execute(
        select(Chat)
        .where(Chat.id == chat_id)
        .options(selectinload(Chat.members))
    )
    return result.scalar_one_or_none()


async def _get_chat_with_members(db: AsyncSession, chat_id: int) -> Chat:
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id).options(selectinload(Chat.members))
    )
    return result.scalar_one()


async def get_or_create_direct_chat(
    db: AsyncSession, user_id: int, other_id: int
) -> Chat:
    result = await db.execute(
        select(Chat)
        .join(ChatMember, Chat.id == ChatMember.chat_id)
        .where(Chat.type == ChatType.direct, ChatMember.user_id == user_id)
        .options(selectinload(Chat.members))
    )
    for chat in result.scalars().all():
        member_ids = {m.user_id for m in chat.members}
        if member_ids == {user_id, other_id}:
            return chat

    chat = Chat(type=ChatType.direct)
    db.add(chat)
    await db.flush()
    db.add(ChatMember(chat_id=chat.id, user_id=user_id))
    db.add(ChatMember(chat_id=chat.id, user_id=other_id))
    await db.commit()
    return await _get_chat_with_members(db, chat.id)


async def create_group_chat(
    db: AsyncSession, group_id: int, member_ids: List[int]
) -> Chat:
    chat = Chat(type=ChatType.group, group_id=group_id)
    db.add(chat)
    await db.flush()
    for uid in member_ids:
        db.add(ChatMember(chat_id=chat.id, user_id=uid))
    await db.commit()
    return await _get_chat_with_members(db, chat.id)


async def get_chat_messages(
    db: AsyncSession, chat_id: int, limit: int = 50, offset: int = 0
) -> List[ChatMessage]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def save_message(
    db: AsyncSession, chat_id: int, sender_id: int, body: str
) -> ChatMessage:
    msg = ChatMessage(chat_id=chat_id, sender_id=sender_id, body=body)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg
