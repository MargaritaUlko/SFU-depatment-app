from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.announcement import AnnouncementStatus


class AttachmentOut(BaseModel):
    id: int
    filename: str
    original_name: str
    content_type: Optional[str]
    size_bytes: Optional[int]

    model_config = {"from_attributes": True}


class AnnouncementCreate(BaseModel):
    title: str
    content: str
    publish_at: Optional[datetime] = None
    target_group: Optional[str] = None


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    publish_at: Optional[datetime] = None
    target_group: Optional[str] = None
    status: Optional[AnnouncementStatus] = None


class AnnouncementOut(BaseModel):
    id: int
    title: str
    content: str
    status: AnnouncementStatus
    publish_at: Optional[datetime]
    target_group: Optional[str]
    notified_via_max: bool
    author_id: int
    created_at: datetime
    attachments: List[AttachmentOut] = []

    model_config = {"from_attributes": True}