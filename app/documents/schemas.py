import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.users.model import Role


class DocumentRead(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    category: str
    visibility: List[str]
    file_name: str
    uploader_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    visibility: Optional[List[Role]] = None
