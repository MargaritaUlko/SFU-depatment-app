import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin
from app.users.model import User  # noqa


class AnnouncementStatus(str, enum.Enum):
    draft = "draft"
    scheduled = "scheduled"
    published = "published"
    archived = "archived"


announcement_groups = Table(
    "announcement_groups",
    Base.metadata,
    Column(
        "announcement_id",
        UUID,
        ForeignKey("announcements.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "group_id",
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

announcement_streams = Table(
    "announcement_streams",
    Base.metadata,
    Column(
        "announcement_id",
        UUID,
        ForeignKey("announcements.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "stream_id",
        UUID(as_uuid=True),
        ForeignKey("streams.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Announcement(Base, TimestampMixin):
    __tablename__ = "announcements"

    id = Column(UUID, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(UUID, ForeignKey("users.id"), nullable=False)

    status = Column(Enum(AnnouncementStatus), default=AnnouncementStatus.draft)

    publish_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    target_groups = relationship(
        "Group", secondary=announcement_groups, lazy="selectin"
    )
    target_streams = relationship(
        "Stream", secondary=announcement_streams, lazy="selectin"
    )

    author = relationship("User", backref="announcements")
    attachments = relationship(
        "Attachment", back_populates="announcement", cascade="all, delete-orphan"
    )
    event = relationship("Event", back_populates="announcement", uselist=False)
    notifications = relationship(
        "Notification", back_populates="announcement", cascade="all, delete-orphan"
    )


class Attachment(Base, TimestampMixin):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    announcement_id = Column(UUID, ForeignKey("announcements.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    content_type = Column(String(100))
    size_bytes = Column(Integer)

    announcement = relationship("Announcement", back_populates="attachments")
