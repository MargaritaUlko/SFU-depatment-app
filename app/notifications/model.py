import enum
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class NotificationType(str, enum.Enum):
    announce = "announce"
    reminder = "reminder"


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)

    # одно из двух заполнено
    event_id = Column(
        UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=True
    )
    announcement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("announcements.id", ondelete="CASCADE"),
        nullable=True,
    )

    # только для уведомлений события
    type = Column(Enum(NotificationType), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "(event_id IS NOT NULL AND announcement_id IS NULL) OR "
            "(event_id IS NULL AND announcement_id IS NOT NULL)",
            name="ck_notification_single_source",
        ),
        CheckConstraint(
            "(event_id IS NOT NULL AND type IS NOT NULL) OR "
            "(event_id IS NULL AND type IS NULL)",
            name="ck_notification_type_only_for_event",
        ),
        UniqueConstraint("event_id", "type", name="uq_notification_type_per_event"),
    )

    event = relationship("Event", back_populates="notifications")
    announcement = relationship("Announcement", back_populates="notifications")
    receipts = relationship(
        "NotificationReceipt",
        back_populates="notification",
        cascade="all, delete-orphan",
    )


class NotificationReceipt(Base, TimestampMixin):
    __tablename__ = "notification_receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_id = Column(
        UUID(as_uuid=True),
        ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("notification_id", "user_id", name="uq_receipt_per_user"),
    )

    notification = relationship("Notification", back_populates="receipts")
    user = relationship("User", backref="notification_receipts")
