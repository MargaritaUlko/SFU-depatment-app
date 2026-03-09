from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class AttendanceCreate(BaseModel):
    teacher_id: int
    subject: str
    group_name: str
    lesson_date: datetime
    present_students: List[str]  # список имён или ID
    total_students: int
    notes: Optional[str] = None


class AttendanceOut(BaseModel):
    id: int
    starosta_id: int
    teacher_id: int
    subject: str
    group_name: str
    lesson_date: datetime
    present_students: str  # JSON
    total_students: int
    present_count: int
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}