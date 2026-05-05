from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class Lesson(Base, TimestampMixin):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    teacher_name = Column(String(255), nullable=True)
    day = Column(Integer, nullable=False)   # 1–7
    week = Column(Integer, nullable=False)  # 1 = нечёт, 2 = чёт
    time_start = Column(String(10), nullable=False)
    time_end = Column(String(10), nullable=False)
    subject = Column(String(500), nullable=False)
    lesson_type = Column(String(100), nullable=True)
    room = Column(String(200), nullable=True)
    building = Column(String(200), nullable=True)

    group = relationship("Group", backref="lessons")
    teacher = relationship("User", foreign_keys=[teacher_id])

    __table_args__ = (
        UniqueConstraint("group_id", "day", "week", "time_start", "subject", name="uq_lesson"),
    )
