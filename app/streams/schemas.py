import uuid
from datetime import datetime
from pydantic import BaseModel


class StreamCreate(BaseModel):
    name: str
    year: int
    speciality: str


class StreamRead(BaseModel):
    id: uuid.UUID
    name: str
    year: int
    speciality: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
