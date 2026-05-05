from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class Group(Base, TimestampMixin):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    stream_id = Column(
        Integer, ForeignKey("streams.id", ondelete="SET NULL"), nullable=True
    )
    year = Column(Integer, nullable=False)

    stream = relationship("Stream", backref="groups")
    student_profiles = relationship("StudentProfile", back_populates="group")
