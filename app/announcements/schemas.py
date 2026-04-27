from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.announcements.model import AnnouncementStatus


class AnnouncementFilters(BaseModel):
    group_name: Optional[str] = None
    flow_name: Optional[str] = None
    department: Optional[str] = None
    status: Optional[AnnouncementStatus] = None
    skip: int = 0
    limit: int = 50


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
    expires_at: Optional[datetime] = None
    target_group: Optional[str] = None


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    target_group: Optional[str] = None
    publish_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class AnnouncementArchive(BaseModel):
    id: int
    status: AnnouncementStatus


class AnnouncementOut(BaseModel):
    id: int
    title: str
    content: str
    status: AnnouncementStatus
    publish_at: Optional[datetime]
    expires_at: Optional[datetime]
    author_id: UUID
    created_at: datetime
    attachments: List[AttachmentOut] = []

    model_config = {"from_attributes": True}
