from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from ..database import Base

class MessageType(str, enum.Enum):
    """消息类型枚举
    
    Attributes:
        text: 文本消息
        voice: 语音消息
        image: 图片消息
    """
    text = "text"
    voice = "voice"
    image = "image"

class ChatMessageModel(Base):
    """聊天消息模型
    
    Attributes:
        id: 消息ID
        user_id: 用户ID
        type: 消息类型
        content: 消息内容
        is_user: 是否为用户消息
        image_url: 图片URL(可选)
        voice_url: 语音URL(可选)
        transcribed_text: 语音转写文本(可选)
        analysis_result: 分析结果(可选)
        suggestions: 建议列表(可选,逗号分隔)
        created_at: 创建时间
    """
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    type = Column(SQLEnum(MessageType), nullable=False)
    content = Column(Text, nullable=False)
    is_user = Column(Boolean, default=True)
    image_url = Column(String(255))
    voice_url = Column(String(255))
    transcribed_text = Column(Text)
    analysis_result = Column(Text)
    suggestions = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now())
    
    # 关系
    user = relationship("User", back_populates="chat_messages") 