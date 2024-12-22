from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from src.database import Base

class MessageType(str, enum.Enum):
    text = "text"
    image = "image"
    voice = "voice"

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(Enum(MessageType))
    content = Column(Text)
    image_url = Column(String, nullable=True)
    voice_url = Column(String, nullable=True)
    is_user = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="messages")

class Suggestion(Base):
    __tablename__ = "suggestions"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    content = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 