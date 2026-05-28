from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.rooms.schemas import RoomRead


class EventCreate(BaseModel):
    title: str
    annotation: Optional[str] = None
    starts_at: datetime
    ends_at: datetime
    room_id: Optional[int] = None
    announcement_id: Optional[int] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    annotation: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    room_id: Optional[int] = None
    announcement_id: Optional[int] = None


class EventRead(BaseModel):
    id: int
    title: str
    annotation: Optional[str] = None
    starts_at: datetime
    ends_at: datetime
    room: Optional[RoomRead] = None
    image_url: Optional[str] = None
    creator_id: int
    announcement_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
