from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, model_validator


class AttendanceCreate(BaseModel):
    teacher_id: Optional[UUID] = None
    group_id: UUID
    subject: str
    lesson_date: datetime
    present_student_ids: List[UUID]
    total_students: int
    notes: Optional[str] = None


class AttendanceOut(BaseModel):
    id: UUID
    starosta_id: UUID
    teacher_id: Optional[UUID]
    group_id: UUID
    subject: str
    lesson_date: datetime
    present_student_ids: List[UUID]
    total_students: int
    present_count: int
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
