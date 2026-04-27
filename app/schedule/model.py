import uuid

from sqlalchemy import CheckConstraint, Column, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    time = Column(String())
    subject = Column(String())
    place = Column(String())
    building = Column(String())
    room_id = Column(String())
    sync = Column(String())
    group_id = Column(String())
    day = Column(Integer())
    week = Column(Integer())

    __table_args__ = (
        CheckConstraint("day >= 1 AND day <= 7", name="check_day_range"),
        CheckConstraint("week >= 1 AND week <= 2", name="check_week_range"),
    )
