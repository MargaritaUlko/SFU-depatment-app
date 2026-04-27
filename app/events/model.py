import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin
from app.rooms.model import Room  # noqa


class Event(Base, TimestampMixin):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    announcement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("announcements.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    title = Column(String(255), nullable=False)
    annotation = Column(Text, nullable=True)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    address = Column(String(500), nullable=True)
    room_id = Column(
        UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True
    )

    image_url = Column(String(500), nullable=True)
    creator_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    room = relationship("Room", back_populates="events")
    creator = relationship("User", backref="events")
    announcement = relationship("Announcement", back_populates="event")
    notifications = relationship(
        "Notification", back_populates="event", cascade="all, delete-orphan"
    )
