# import enum

# from sqlalchemy import Column, String, Text, Enum, ForeignKey, Integer
# from sqlalchemy.orm import relationship

# from app.db.base import Base, TimestampMixin


# class TargetType(str, enum.Enum):
#     group = "group"
#     stream = "stream"


# class Message(Base, TimestampMixin):
#     __tablename__ = "messages"

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
#     target_type = Column(Enum(TargetType, name="targettype"), nullable=False)
#     target_id = Column(Integer, nullable=False)
#     subject = Column(String(255), nullable=False)
#     body = Column(Text, nullable=False)

#     sender = relationship("User", backref="messages")
