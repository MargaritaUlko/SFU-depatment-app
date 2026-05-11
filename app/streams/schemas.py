from typing import Optional

from pydantic import BaseModel


class StreamCreate(BaseModel):
    name: str
    year: int
    speciality: str


class StreamUpdate(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    speciality: Optional[str] = None


class StreamRead(BaseModel):
    id: int
    name: str
    year: int
    speciality: str

    model_config = {"from_attributes": True}
