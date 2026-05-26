import enum

from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class VKRStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class VKRTopic(Base, TimestampMixin):
    __tablename__ = "vkr_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    proposed_by_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum(VKRStatus, name="vkrstatus"), default=VKRStatus.pending, nullable=False)
    head_comment = Column(Text, nullable=True)

    proposed_by = relationship("User", foreign_keys=[proposed_by_id])
    student = relationship("User", foreign_keys=[student_id])
