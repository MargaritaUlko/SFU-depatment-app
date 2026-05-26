from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.chat.model import ChatType


class GroupChatCreate(BaseModel):
    group_id: int
    member_ids: List[int]


class ChatMemberRead(BaseModel):
    user_id: int
    model_config = {"from_attributes": True}


class ChatRead(BaseModel):
    id: int
    type: ChatType
    group_id: Optional[int] = None
    members: List[ChatMemberRead] = []
    model_config = {"from_attributes": True}


class ChatMessageCreate(BaseModel):
    body: str


class ChatMessageRead(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    body: str
    created_at: datetime
    model_config = {"from_attributes": True}
