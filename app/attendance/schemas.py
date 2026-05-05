from datetime import datetime

from pydantic import BaseModel


class AttendanceOut(BaseModel):
    id: int
    lesson_id: int
    student_id: int
    marked_via: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AttendanceTokenOut(BaseModel):
    id: int
    lesson_id: int
    token: str
    expires_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}
