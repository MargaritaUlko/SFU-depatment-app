import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class GroupCreate(BaseModel):
    name: str
    stream_id: Optional[uuid.UUID] = None
    year: int
    sfu_timetable_name: str


class GroupRead(BaseModel):
    id: uuid.UUID
    name: str
    stream_id: Optional[uuid.UUID]
    year: int
    sfu_timetable_name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
