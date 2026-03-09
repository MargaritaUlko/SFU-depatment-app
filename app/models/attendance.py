from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin


class AttendanceReport(Base, TimestampMixin):
    __tablename__ = "attendance_reports"

    id = Column(Integer, primary_key=True, index=True)

    # Кто отправил (только starosta)
    starosta_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Кому адресовано (преподаватель)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    subject = Column(String(255), nullable=False)
    group_name = Column(String(100), nullable=False)
    lesson_date = Column(DateTime(timezone=True), nullable=False)

    # JSON-список присутствующих (имена / студенческие ID)
    present_students = Column(Text, nullable=False)  # JSON string
    total_students = Column(Integer, nullable=False)
    present_count = Column(Integer, nullable=False)

    notes = Column(Text, nullable=True)

    starosta = relationship("User", foreign_keys=[starosta_id])
    teacher = relationship("User", foreign_keys=[teacher_id])