import uuid

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class Group(Base, TimestampMixin):
    __tablename__ = "groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    stream_id = Column(
        UUID(as_uuid=True), ForeignKey("streams.id", ondelete="SET NULL"), nullable=True
    )
    year = Column(Integer, nullable=False)
    schedule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("schedules.id"),
        nullable=True,
    )

    stream = relationship("Stream", backref="groups")
    student_profiles = relationship("StudentProfile", back_populates="group")
    schedule = relationship("Schedule", backref="group")
