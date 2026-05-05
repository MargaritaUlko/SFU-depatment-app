from typing import Optional

from pydantic import BaseModel


class LessonOut(BaseModel):
    id: int
    group_id: int
    teacher_id: Optional[int]
    teacher_name: Optional[str]
    day: int
    week: int
    time_start: str
    time_end: str
    subject: str
    lesson_type: Optional[str]
    room: Optional[str]
    building: Optional[str]

    model_config = {"from_attributes": True}


class SyncResult(BaseModel):
    created: int
    skipped: int
    errors: list[str]
