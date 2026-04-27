import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.users.model import Role


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Role = Role.student


class UserRead(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: Role
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class UserRoleUpdate(BaseModel):
    role: Role
