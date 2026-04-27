import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class AttendanceReport(Base, TimestampMixin):
    __tablename__ = "attendance_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    starosta_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=False)

    subject = Column(String(255), nullable=False)
    lesson_date = Column(DateTime(timezone=True), nullable=False)

    # UUID студентов из таблицы users, пришедших на занятие
    present_student_ids = Column(
        ARRAY(UUID(as_uuid=True)), nullable=False, default=list
    )
    total_students = Column(Integer, nullable=False)
    present_count = Column(Integer, nullable=False)

    notes = Column(Text, nullable=True)

    starosta = relationship("User", foreign_keys=[starosta_id])
    teacher = relationship("User", foreign_keys=[teacher_id])
    group = relationship("Group")
