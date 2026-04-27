import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.groups.model import Group
from app.groups.schemas import GroupCreate


async def get_groups(db: AsyncSession) -> List[Group]:
    result = await db.execute(select(Group).options(selectinload(Group.stream)))
    return list(result.scalars().all())


async def get_group(db: AsyncSession, group_id: uuid.UUID) -> Optional[Group]:
    result = await db.execute(
        select(Group).where(Group.id == group_id).options(selectinload(Group.stream))
    )
    return result.scalar_one_or_none()


async def create_group(db: AsyncSession, data: GroupCreate) -> Group:
    group = Group(**data.model_dump())
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group
