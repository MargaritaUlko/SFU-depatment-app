from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.lessons.model import Lesson


async def get_lessons_by_group(
    db: AsyncSession, group_id: int, week: Optional[int] = None
) -> list[Lesson]:
    q = select(Lesson).where(Lesson.group_id == group_id)
    if week is not None:
        q = q.where(Lesson.week == week)
    q = q.order_by(Lesson.day, Lesson.time_start)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_lessons_by_teacher(
    db: AsyncSession, teacher_id: int, week: Optional[int] = None
) -> list[Lesson]:
    q = select(Lesson).where(Lesson.teacher_id == teacher_id)
    if week is not None:
        q = q.where(Lesson.week == week)
    q = q.order_by(Lesson.day, Lesson.time_start)
    result = await db.execute(q)
    return list(result.scalars().all())
