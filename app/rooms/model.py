from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class Room(Base, TimestampMixin):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(String(100), nullable=False)
    address = Column(String(500), nullable=False)
    capacity = Column(Integer, nullable=True)

    events = relationship("Event", back_populates="room")
