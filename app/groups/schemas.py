from typing import Optional

from pydantic import BaseModel


class GroupCreate(BaseModel):
    name: str
    stream_id: int
    year: int


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    stream_id: Optional[int] = None
    year: Optional[int] = None


class GroupRead(BaseModel):
    id: int
    name: str
    stream_id: Optional[int]
    year: int

    model_config = {"from_attributes": True}
