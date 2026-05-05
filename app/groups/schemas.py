from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GroupCreate(BaseModel):
    name: str
    stream_id: int
    year: int


class GroupRead(BaseModel):
    id: int
    name: str
    stream_id: Optional[int]
    year: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
