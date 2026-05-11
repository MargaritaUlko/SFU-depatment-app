import enum

from sqlalchemy import Column, Enum, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class ChatType(str, enum.Enum):
    group = "group"
    direct = "direct"


class Chat(Base, TimestampMixin):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(Enum(ChatType, name="chattype"), nullable=False)
    group_id = Column(
        Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=True, unique=True
    )

    group = relationship("Group", backref="chat")
    members = relationship(
        "ChatMember", back_populates="chat", cascade="all, delete-orphan", lazy="selectin"
    )
    messages = relationship(
        "ChatMessage", back_populates="chat", cascade="all, delete-orphan"
    )


class ChatMember(Base):
    __tablename__ = "chat_members"
    __table_args__ = (UniqueConstraint("chat_id", "user_id"),)

    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    chat = relationship("Chat", back_populates="members")
    user = relationship("User")


class ChatMessage(Base, TimestampMixin):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    body = Column(Text, nullable=False)

    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User")
