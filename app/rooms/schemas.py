from typing import Optional

from pydantic import BaseModel


class RoomCreate(BaseModel):
    number: str
    address: str
    capacity: Optional[int]


class RoomUpdate(RoomCreate):
    schedule_id: Optional[int] = None


class RoomRead(RoomUpdate):
    id: int
