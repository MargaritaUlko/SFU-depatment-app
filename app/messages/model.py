import uuid
import enum
from sqlalchemy import Column, String, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin


class TargetType(str, enum.Enum):
    group = "group"
    stream = "stream"


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_type = Column(Enum(TargetType, name="targettype"), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)

    sender = relationship("User", backref="messages")
