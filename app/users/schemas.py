from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.users.model import Role, TeacherPosition


class StudentRegister(BaseModel):
    name: str
    surname: str
    patronymic: Optional[str] = None
    email: EmailStr
    password: str
    group_id: int


class UserCreate(BaseModel):
    name: str
    surname: str
    patronymic: Optional[str] = None
    email: EmailStr
    password: Optional[str] = None
    role: Role = Role.student


class UserRead(BaseModel):
    id: int
    name: str
    surname: str
    patronymic: Optional[str]
    email: EmailStr
    role: Role
    is_active: bool
    avatar: Optional[str] = Field(default=None, json_schema_extra={"example": None})
    created_at: datetime
    updated_at: datetime

    # model_config = {"from_attributes": True}


class TeacherPublicRead(BaseModel):
    id: int
    name: str
    surname: str
    patronymic: Optional[str]
    role: Role
    avatar: Optional[str] = None
    department: Optional[str] = None
    positions: Optional[List[TeacherPosition]] = None
    cabinet: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    patronymic: Optional[str] = None
    email: Optional[EmailStr] = None


class StudentProfileUpdate(BaseModel):
    phone: Optional[str] = None
    telegram: Optional[str] = None
    vk: Optional[str] = None


class StudentGroupUpdate(BaseModel):
    group_id: int


class TeacherProfileUpdate(BaseModel):
    department: Optional[str] = None
    positions: Optional[List[TeacherPosition]] = None
    phone: Optional[str] = None
    cabinet: Optional[str] = None


class DeanProfileUpdate(BaseModel):
    faculty: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    cabinet: Optional[str] = None


class UserPasswordChange(BaseModel):
    old_password: str
    new_password: str


class StudentProfileRead(BaseModel):
    group_id: int
    group_name: Optional[str] = None
    phone: Optional[str] = None
    telegram: Optional[str] = None
    vk: Optional[str] = None


class TeacherProfileRead(BaseModel):
    department: Optional[str] = None
    positions: Optional[List[TeacherPosition]] = None
    phone: Optional[str] = None
    cabinet: Optional[str] = None


class DeanProfileRead(BaseModel):
    faculty: str
    position: Optional[str] = None
    phone: Optional[str] = None
    cabinet: Optional[str] = None


class _MeBase(BaseModel):
    id: int
    name: str
    surname: str
    patronymic: Optional[str] = None
    email: EmailStr
    role: Role
    is_active: bool
    avatar: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class StudentMeResponse(_MeBase):
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    phone: Optional[str] = None
    telegram: Optional[str] = None
    vk: Optional[str] = None


class TeacherMeResponse(_MeBase):
    department: Optional[str] = None
    positions: Optional[List[TeacherPosition]] = None
    phone: Optional[str] = None
    cabinet: Optional[str] = None


class DeanMeResponse(_MeBase):
    faculty: Optional[str] = None
    dean_position: Optional[str] = None
    phone: Optional[str] = None
    cabinet: Optional[str] = None
