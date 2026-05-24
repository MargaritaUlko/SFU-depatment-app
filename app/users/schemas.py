from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.users.model import Role


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


class UserUpdate(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    patronymic: Optional[str] = None
    email: Optional[EmailStr] = None


class UserPasswordChange(BaseModel):
    old_password: str
    new_password: str
