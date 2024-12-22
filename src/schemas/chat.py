from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from src.models.chat import MessageType

class MessageBase(BaseModel):
    content: str
    type: MessageType = MessageType.text
    image_url: Optional[str] = None
    voice_url: Optional[str] = None

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    user_id: int
    is_user: bool
    created_at: datetime

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    message: str
    suggestions: Optional[List[str]] = None
    image_url: Optional[str] = None
    voice_url: Optional[str] = None

class TextRequest(BaseModel):
    message: str

class ImageRequest(BaseModel):
    image_url: str

class VoiceRequest(BaseModel):
    voice_url: str

class MessageHistory(BaseModel):
    messages: List[Message]

    class Config:
        from_attributes = True 