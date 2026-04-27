import uuid
from sqlalchemy import Column, String, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    visibility = Column(JSON, nullable=False, default=list)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    uploader_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    uploader = relationship("User", backref="documents")
