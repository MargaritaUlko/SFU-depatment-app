import uuid

from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class Room(Base, TimestampMixin):
    __tablename__ = "rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    address = Column(String(500), nullable=True)
    capacity = Column(Integer, nullable=True)

    events = relationship("Event", back_populates="room")
    schedule = relationship("Schedule", backref="room")
