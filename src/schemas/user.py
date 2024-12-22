from pydantic import BaseModel, EmailStr, Field, ConfigDict, validator
from typing import Optional
from datetime import datetime
import re

class UserBase(BaseModel):
    """用户基础模型
    
    包含用户的基本信息字段
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="用户名，3-50个字符"
    )
    email: EmailStr = Field(
        ...,
        description="电子邮件地址"
    )

class UserCreate(UserBase):
    """用户创建模型
    
    用于用户注册的数据验证
    """
    password: str = Field(
        ...,
        min_length=6,
        description="密码，最少6个字符"
    )
    confirm_password: str = Field(
        ...,
        min_length=6,
        description="确认密码"
    )
    
    @validator('email')
    def validate_email(cls, v):
        """验证邮箱格式是否合法
        
        Args:
            v: 邮箱地址
            
        Returns:
            str: 验证通过的邮箱地址
            
        Raises:
            ValueError: 当邮箱格式不合法时抛出
        """
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, str(v)):
            raise ValueError('邮箱格式不正确')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        """验证两次输入的密码是否匹配
        
        Args:
            v: 确认密码值
            values: 已验证的字段值
            
        Returns:
            str: 验证通过的确认密码
            
        Raises:
            ValueError: 当密码不匹配时抛出
        """
        if 'password' in values and v != values['password']:
            raise ValueError('两次输入的密码不匹配')
        return v

class UserLogin(BaseModel):
    """用户登录模型
    
    用于用户登录的数据验证
    """
    username: str = Field(
        ...,
        description="用户名"
    )
    password: str = Field(
        ...,
        description="密码"
    )

class UserResponse(UserBase):
    """用户响应模型
    
    用于返回用户信息的数据格式
    """
    id: str = Field(
        ...,
        description="用户ID"
    )
    is_active: bool = Field(
        ...,
        description="用户状态"
    )
    created_at: datetime = Field(
        ...,
        description="创建时间"
    )
    
    # 配置从ORM模型转换
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    """令牌模型
    
    用于返回认证令牌的数据格式
    """
    access_token: str = Field(
        ...,
        description="访问令牌"
    )
    token_type: str = Field(
        "bearer",
        description="令牌类型"
    )
    refresh_token: Optional[str] = Field(
        None,
        description="刷新令牌"
    )

class TokenData(BaseModel):
    """令牌数据模型
    
    用于存储令牌中的用户信息
    """
    username: Optional[str] = Field(
        None,
        description="用户名"
    )
    exp: Optional[datetime] = Field(
        None,
        description="过期时间"
    )