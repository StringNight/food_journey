"""聊天相关的schema定义"""

from pydantic import BaseModel, Field, constr
from typing import Optional, List, Dict, Any
from datetime import datetime

class TextRequest(BaseModel):
    """文本消息请求
    
    Attributes:
        message: 消息内容，不能为空，长度在1-1000字符之间
    """
    message: str = Field(..., description="消息内容，不能为空，长度在1-1000字符之间")

class VoiceRequest(BaseModel):
    """语音消息请求
    
    Attributes:
        language: 语音语言,默认为中文
    """
    language: str = Field(default="zh", description="语音语言")

class ImageRequest(BaseModel):
    """图片消息请求
    
    Attributes:
        description: 图片描述(可选)
    """
    description: Optional[str] = Field(None, description="图片描述")

class MessageResponse(BaseModel):
    """消息响应
    
    Attributes:
        schema_version: schema版本号
        message: 消息内容
        suggestions: 建议列表(可选)
        voice_url: 语音URL(可选)
        image_url: 图片URL(可选)
        transcribed_text: 语音转写文本(可选)
        analysis_result: 分析结果(可选)
        created_at: 创建时间(可选)
        is_user: 是否为用户消息(可选)
        history: 历史消息列表(可选)，按时间正序排列
    """
    schema_version: str = Field(..., description="schema版本号")
    message: str = Field(..., description="消息内容")
    suggestions: Optional[List[str]] = Field(default=[], description="建议列表")
    voice_url: Optional[str] = Field(None, description="语音URL")
    image_url: Optional[str] = Field(None, description="图片URL")
    transcribed_text: Optional[str] = Field(None, description="语音转写文本")
    analysis_result: Optional[str] = Field(None, description="分析结果")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    is_user: Optional[bool] = Field(None, description="是否为用户消息")
    history: Optional[List[Dict[str, Any]]] = Field(default=[], description="历史消息列表，按时间正序排列")

class PaginationInfo(BaseModel):
    """分页信息
    
    Attributes:
        page: 当前页码
        per_page: 每页记录数
        total: 总记录数
        total_pages: 总页数
    """
    page: int = Field(..., description="当前页码")
    per_page: int = Field(..., description="每页记录数")
    total: int = Field(..., description="总记录数")
    total_pages: int = Field(..., description="总页数")

class MessageHistory(BaseModel):
    """聊天历史
    
    Attributes:
        schema_version: schema版本号
        messages: 消息列表
        pagination: 分页信息
    """
    schema_version: str = Field(..., description="schema版本号")
    messages: List[MessageResponse] = Field(..., description="消息列表")
    pagination: PaginationInfo = Field(..., description="分页信息") 