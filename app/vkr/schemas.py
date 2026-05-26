from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.vkr.model import VKRStatus


class ProposerBrief(BaseModel):
    id: int
    name: str
    surname: str
    patronymic: Optional[str]

    model_config = {"from_attributes": True}


class VKRTopicCreate(BaseModel):
    title: str
    description: Optional[str] = None


class VKRTopicRead(BaseModel):
    id: int
    title: str
    description: Optional[str]
    proposed_by_id: int
    proposed_by: ProposerBrief
    student_id: Optional[int]
    status: VKRStatus
    head_comment: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VKRTopicReview(BaseModel):
    approved: bool
    comment: Optional[str] = None
