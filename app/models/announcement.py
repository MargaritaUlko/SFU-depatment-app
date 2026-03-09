import enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin


class AnnouncementStatus(str, enum.Enum):
    draft = "draft"
    scheduled = "scheduled"
    published = "published"
    archived = "archived"


class Announcement(Base, TimestampMixin):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    status = Column(Enum(AnnouncementStatus), default=AnnouncementStatus.draft)

    # Расписание публикации
    publish_at = Column(DateTime(timezone=True), nullable=True)

    # Кому адресовано: всем / конкретной группе
    target_group = Column(String(100), nullable=True)  # None = всем

    # Отправлено ли в Max
    notified_via_max = Column(Boolean, default=False)

    author = relationship("User", backref="announcements")
    attachments = relationship("Attachment", back_populates="announcement", cascade="all, delete-orphan")


class Attachment(Base, TimestampMixin):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    announcement_id = Column(Integer, ForeignKey("announcements.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    content_type = Column(String(100))
    size_bytes = Column(Integer)

    announcement = relationship("Announcement", back_populates="attachments")