from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class Attendance(Base, TimestampMixin):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(
        Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    student_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    marked_via = Column(String(10), nullable=False, default="qr")  # "qr" | "manual"

    student = relationship("User", foreign_keys=[student_id])

    __table_args__ = (UniqueConstraint("lesson_id", "student_id"),)


class AttendanceToken(Base, TimestampMixin):
    __tablename__ = "attendance_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(
        Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    token = Column(String, unique=True, nullable=False, default=lambda: str(uuid4()))
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)

    lesson = relationship("Lesson", backref="attendance_tokens")
