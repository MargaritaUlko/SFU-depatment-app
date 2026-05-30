from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, require_roles
from app.users.model import Role
from app.vkr import service
from app.vkr.crud import delete_topics
from app.vkr.model import VKRStatus
from app.vkr.schemas import VKRTopicCreate, VKRTopicRead, VKRTopicReview

router = APIRouter(prefix="/vkr", tags=["vkr"])

_PROPOSER_ROLES = (Role.student, Role.headman, Role.teacher, Role.deputy_head)


@router.post(
    "/topics", response_model=VKRTopicRead, status_code=status.HTTP_201_CREATED
)
async def propose_topic(
    data: VKRTopicCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(*_PROPOSER_ROLES)),
):
    return await service.propose(db, data, current_user)


@router.get("/my-topics", response_model=List[VKRTopicRead])
async def my_topics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await service.get_my_topics(db, current_user)


@router.get("/topics/approved", response_model=List[VKRTopicRead])
async def approved_topics(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(Role.dean, Role.deputy_head, Role.admin)),
):
    return await service.get_approved(db)


@router.get("/topics", response_model=List[VKRTopicRead])
async def list_all_topics(
    status_filter: Optional[VKRStatus] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(Role.deputy_head, Role.admin)),
):
    return await service.get_all(db, status_filter)


@router.get("/topics/{topic_id}", response_model=VKRTopicRead)
async def topic_detail(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await service.get_detail(db, topic_id, current_user)


@router.delete("/topics", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_delete_topics(
    ids: Optional[List[int]] = Query(None, description="ID тем для удаления. Если не указаны — удаляются все темы."),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(Role.deputy_head, Role.admin)),
):
    await delete_topics(db, ids=ids or None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/topics/{topic_id}/review", response_model=VKRTopicRead)
async def review_topic(
    topic_id: int,
    data: VKRTopicReview,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles(Role.deputy_head)),
):
    return await service.review(db, topic_id, data)
