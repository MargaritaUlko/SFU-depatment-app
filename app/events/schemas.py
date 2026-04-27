import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class EventLinkCreate(BaseModel):
    title: str
    url: str


class EventLinkRead(BaseModel):
    id: uuid.UUID
    title: str
    url: str

    model_config = {"from_attributes": True}


class EventCreate(BaseModel):
    title: str
    annotation: Optional[str] = None
    starts_at: datetime
    ends_at: datetime
    location: Optional[str] = None
    links: List[EventLinkCreate] = []


class EventUpdate(BaseModel):
    title: Optional[str] = None
    annotation: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    location: Optional[str] = None
    links: Optional[List[EventLinkCreate]] = None


class EventRead(BaseModel):
    id: uuid.UUID
    title: str
    annotation: Optional[str]
    starts_at: datetime
    ends_at: datetime
    location: Optional[str]
    image_url: Optional[str]
    creator_id: uuid.UUID
    links: List[EventLinkRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
