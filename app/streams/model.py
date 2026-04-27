import uuid
from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin


class Stream(Base, TimestampMixin):
    __tablename__ = "streams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    speciality = Column(String(255), nullable=False)

    def __str__(self) -> str:
        return self.name
