from datetime import datetime

from pydantic import BaseModel

from app.messages.model import TargetType


class MessageCreate(BaseModel):
    target_type: TargetType
    target_id: int
    subject: str
    body: str


class MessageRead(BaseModel):
    id: int
    sender_id: int
    target_type: TargetType
    target_id: int
    subject: str
    body: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
