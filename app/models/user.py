import uuid
import enum
from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin


class Role(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    head = "head"
    admin = "admin"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(Role, name="role"), default=Role.student, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
