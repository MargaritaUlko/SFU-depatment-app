from datetime import datetime, timezone
from typing import List, Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_serializer

KRK_TZ = ZoneInfo("Asia/Krasnoyarsk")

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
    publish_at: Optional[datetime] = Field(default=None, examples=["2026-06-01T10:00:00+07:00"])
    expires_at: Optional[datetime] = Field(default=None, examples=["2026-06-08T10:00:00+07:00"])
    target_group_ids: Optional[List[int]] = None
    target_stream_ids: Optional[List[int]] = None


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    target_group_ids: Optional[List[int]] = None
    target_stream_ids: Optional[List[int]] = None
    publish_at: Optional[datetime] = Field(default=None, examples=["2026-06-01T10:00:00+07:00"])
    expires_at: Optional[datetime] = Field(default=None, examples=["2026-06-08T10:00:00+07:00"])


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
    author_id: int
    created_at: datetime
    attachments: List[AttachmentOut] = []

    model_config = {"from_attributes": True}

    @field_serializer("publish_at", "expires_at", "created_at")
    def to_krasnoyarsk(self, v: Optional[datetime]) -> Optional[str]:
        if v is None:
            return None
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v.astimezone(KRK_TZ).isoformat()
