from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.model import Role, User
from app.vkr.crud import (
    create_topic,
    get_all_topics,
    get_topic,
    get_topics_by_proposer,
    review_topic,
)
from app.vkr.model import VKRStatus, VKRTopic
from app.vkr.schemas import VKRTopicCreate, VKRTopicReview

_PRIVILEGED = (Role.deputy_head, Role.admin, Role.dean)


async def propose(
    db: AsyncSession,
    data: VKRTopicCreate,
    current_user: User,
) -> VKRTopic:
    student_id = current_user.id if current_user.role in (Role.student, Role.headman) else None
    return await create_topic(db, data, proposed_by_id=current_user.id, student_id=student_id)


async def get_my_topics(db: AsyncSession, current_user: User) -> List[VKRTopic]:
    return await get_topics_by_proposer(db, current_user.id)


async def get_all(
    db: AsyncSession,
    status_filter: Optional[VKRStatus],
) -> List[VKRTopic]:
    return await get_all_topics(db, status=status_filter)


async def get_approved(db: AsyncSession) -> List[VKRTopic]:
    return await get_all_topics(db, status=VKRStatus.approved)


async def get_detail(
    db: AsyncSession,
    topic_id: int,
    current_user: User,
) -> VKRTopic:
    topic = await get_topic(db, topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тема не найдена")
    if current_user.role not in _PRIVILEGED and topic.proposed_by_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return topic


async def review(
    db: AsyncSession,
    topic_id: int,
    data: VKRTopicReview,
) -> VKRTopic:
    topic = await get_topic(db, topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тема не найдена")
    if topic.status != VKRStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Тема уже рассмотрена",
        )
    if not data.approved and not data.comment:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="При отклонении необходимо указать комментарий",
        )
    return await review_topic(db, topic, data.approved, data.comment)
