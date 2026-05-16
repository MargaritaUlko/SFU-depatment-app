import enum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class Role(str, enum.Enum):
    student = "student"
    headman = "headman"  # староста
    teacher = "teacher"
    dean = "dean"  # деканат
    admin = "admin"
    deputy_head = "deputy_head"


class TeacherPosition(str, enum.Enum):
    assistant = "assistant"  # ассистент
    lecturer = "lecturer"  # преподаватель
    senior_lecturer = "senior_lecturer"  # старший преподаватель
    associate_professor = "associate_professor"  # доцент
    professor = "professor"  # профессор
    sfu_professor = "sfu_professor"  # профессор СФУ
    acting_head = "acting_head"  # и.о. заведующего кафедрой


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    surname = Column(String(100))
    patronymic = Column(String(100), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(Role, name="role"), default=Role.student, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    avatar = Column(String(500), nullable=True)
    student_profiles = relationship(
        "StudentProfile", back_populates="user", uselist=False
    )
    teacher_profile = relationship(
        "TeacherProfile", back_populates="user", uselist=False
    )
    dean_profile = relationship("DeanProfile", back_populates="user", uselist=False)


class StudentProfile(Base, TimestampMixin):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    phone = Column(String(20), nullable=True)
    telegram = Column(String(100), nullable=True)
    vk = Column(String(100), nullable=True)

    user = relationship("User", back_populates="student_profiles")
    group = relationship("Group", back_populates="student_profiles")


class TeacherProfile(Base, TimestampMixin):
    __tablename__ = "teacher_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    department = Column(String(255), nullable=True)
    positions = Column(
        ARRAY(SAEnum(TeacherPosition, name="teacher_position")), nullable=True
    )

    phone = Column(String(20), nullable=True)
    cabinet = Column(String(50), nullable=True)

    user = relationship("User", back_populates="teacher_profile")


class DeanProfile(Base, TimestampMixin):
    __tablename__ = "dean_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    faculty = Column(String(255), nullable=False)
    position = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    cabinet = Column(String(50), nullable=True)

    user = relationship("User", back_populates="dean_profile")
