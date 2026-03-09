import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.message import TargetType


class MessageCreate(BaseModel):
    target_type: TargetType
    target_id: uuid.UUID
    subject: str
    body: str


class MessageRead(BaseModel):
    id: uuid.UUID
    sender_id: uuid.UUID
    target_type: TargetType
    target_id: uuid.UUID
    subject: str
    body: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
