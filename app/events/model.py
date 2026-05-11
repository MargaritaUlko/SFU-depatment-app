from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class Event(Base, TimestampMixin):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    announcement_id = Column(
        Integer,
        ForeignKey("announcements.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    title = Column(String(255), nullable=False)
    annotation = Column(Text, nullable=True)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    room_id = Column(
        Integer, ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True
    )

    image_url = Column(String(500), nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    room = relationship("Room", back_populates="events")
    creator = relationship("User", backref="events")
    announcement = relationship("Announcement", back_populates="event")
    notifications = relationship(
        "Notification", back_populates="event", cascade="all, delete-orphan"
    )
