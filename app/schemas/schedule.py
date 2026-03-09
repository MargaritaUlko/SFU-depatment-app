from typing import List, Optional
from pydantic import BaseModel


class ScheduleEntry(BaseModel):
    day: str
    period: int
    time: str
    week_type: str          # "odd" | "even"
    subject: str
    type: str               # "lecture" | "practice" | "lab"
    teacher: str
    location: str
    format: str             # "sync" | "async"


class ScheduleResponse(BaseModel):
    title: str
    lessons: List[ScheduleEntry]
