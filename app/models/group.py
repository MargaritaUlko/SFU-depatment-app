import uuid
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin


class Group(Base, TimestampMixin):
    __tablename__ = "groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    stream_id = Column(UUID(as_uuid=True), ForeignKey("streams.id", ondelete="SET NULL"), nullable=True)
    year = Column(Integer, nullable=False)
    # Строка подставляемая в ?group= при парсинге расписания СФУ
    # Например: 'ВЦ25-01 (1 подгруппа)'
    sfu_timetable_name = Column(String(255), nullable=False)

    stream = relationship("Stream", backref="groups")
