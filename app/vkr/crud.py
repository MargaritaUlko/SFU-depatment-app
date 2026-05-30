from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.vkr.model import VKRStatus, VKRTopic
from app.vkr.schemas import VKRTopicCreate


def _with_relations(stmt):
    return stmt.options(
        selectinload(VKRTopic.proposed_by),
        selectinload(VKRTopic.student),
    )


async def create_topic(
    db: AsyncSession,
    data: VKRTopicCreate,
    proposed_by_id: int,
    student_id: Optional[int] = None,
) -> VKRTopic:
    topic = VKRTopic(
        title=data.title,
        description=data.description,
        proposed_by_id=proposed_by_id,
        student_id=student_id,
        status=VKRStatus.pending,
    )
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    result = await db.execute(
        _with_relations(select(VKRTopic).where(VKRTopic.id == topic.id))
    )
    return result.scalar_one()


async def get_topic(db: AsyncSession, topic_id: int) -> Optional[VKRTopic]:
    result = await db.execute(
        _with_relations(select(VKRTopic).where(VKRTopic.id == topic_id))
    )
    return result.scalar_one_or_none()


async def get_topics_by_proposer(db: AsyncSession, user_id: int) -> List[VKRTopic]:
    result = await db.execute(
        _with_relations(
            select(VKRTopic)
            .where(VKRTopic.proposed_by_id == user_id)
            .order_by(VKRTopic.created_at.desc())
        )
    )
    return list(result.scalars().all())


async def get_all_topics(
    db: AsyncSession,
    status: Optional[VKRStatus] = None,
) -> List[VKRTopic]:
    stmt = select(VKRTopic).order_by(VKRTopic.created_at.desc())
    if status is not None:
        stmt = stmt.where(VKRTopic.status == status)
    result = await db.execute(_with_relations(stmt))
    return list(result.scalars().all())


async def delete_topics(
    db: AsyncSession,
    ids: Optional[List[int]] = None,
) -> int:
    stmt = delete(VKRTopic)
    if ids:
        stmt = stmt.where(VKRTopic.id.in_(ids))
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount


async def review_topic(
    db: AsyncSession,
    topic: VKRTopic,
    approved: bool,
    comment: Optional[str],
) -> VKRTopic:
    topic.status = VKRStatus.approved if approved else VKRStatus.rejected
    topic.head_comment = comment
    await db.commit()
    await db.refresh(topic)
    result = await db.execute(
        _with_relations(select(VKRTopic).where(VKRTopic.id == topic.id))
    )
    return result.scalar_one()
