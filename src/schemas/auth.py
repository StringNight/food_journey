from pydantic import BaseModel, validator, Field
from typing import Optional, List, Union
from datetime import datetime
import re

class UserBase(BaseModel):
    """用户基本信息模型"""
    username: str = Field(
        ...,
        min_length=3,
        max_length=32,
        pattern=r'^[a-zA-Z0-9_-]+$',
        description="用户名，3-32个字符，只能包含字母、数字、下划线和连字符"
    )

class UserCreate(UserBase):
    """用户注册请求模型"""
    password: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="密码，8-64个字符，必须包含大小写字母、数字和特殊字符"
    )

    @validator('password')
    def validate_password(cls, v):
        """验证密码格式
        
        要求:
        1. 至少8个字符
        2. 至少包含一个大写字母
        3. 至少包含一个小写字母
        4. 至少包含一个数字
        5. 至少包含一个特殊字符
        """
        if not re.search(r'[A-Z]', v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not re.search(r'[a-z]', v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含至少一个数字')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('密码必须包含至少一个特殊字符')
        return v

    @validator('username')
    def validate_username(cls, v):
        """验证用户名格式"""
        if not v.strip():
            raise ValueError('用户名不能为空')
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v

class UserLogin(BaseModel):
    """用户登录请求模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

class ChangePassword(BaseModel):
    """密码修改请求模型"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="新密码，8-64个字符，必须包含大小写字母、数字和特殊字符"
    )

    @validator('new_password')
    def validate_new_password(cls, v):
        """验证新密码格式"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not re.search(r'[a-z]', v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含至少一个数字')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('密码必须包含至少一个特殊字符')
        return v

class Token(BaseModel):
    """令牌响应模型"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="令牌过期时间（秒）")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }

class TokenData(BaseModel):
    """令牌数据模型"""
    user_id: str = Field(..., description="用户ID")
    exp: int = Field(..., description="过期时间（Unix时间戳）")
    iat: int = Field(..., description="创建时间（Unix时间戳）")
    jti: str = Field(..., description="令牌唯一标识")
    token_version: int = Field(default=1, description="令牌版本，用于实现令牌撤销")

class UserResponse(BaseModel):
    """用户信息响应模型"""
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    is_active: bool = Field(default=True, description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    login_count: int = Field(default=0, description="登录次数")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "testuser",
                "avatar_url": "http://example.com/avatar.jpg",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00",
                "last_login": "2024-01-02T10:30:00",
                "login_count": 5
            }
        }

    def dict(self, *args, **kwargs):
        """重写dict方法以处理datetime序列化"""
        d = super().dict(*args, **kwargs)
        for field in ['created_at', 'last_login']:
            if isinstance(d.get(field), datetime):
                d[field] = d[field].isoformat()
        return d

class LoginJsonResponse(BaseModel):
    """JSON格式登录响应模型"""
    token: Token = Field(..., description="访问令牌信息")
    user: UserResponse = Field(..., description="用户信息")

    def model_dump(self, *args, **kwargs):
        """重写model_dump方法以处理datetime序列化"""
        d = super().model_dump(*args, **kwargs)
        if 'user' in d:
            if isinstance(d['user'].get('created_at'), datetime):
                d['user']['created_at'] = d['user']['created_at'].isoformat()
            if isinstance(d['user'].get('last_login'), datetime):
                d['user']['last_login'] = d['user']['last_login'].isoformat()
        return d

    class Config:
        json_schema_extra = {
            "example": {
                "token": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 3600
                },
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "username": "testuser",
                    "avatar_url": "http://example.com/avatar.jpg",
                    "is_active": True,
                    "created_at": "2024-01-01T00:00:00",
                    "last_login": "2024-01-02T10:30:00",
                    "login_count": 5
                }
            }
        }

class RegisterResponse(BaseModel):
    """注册响应模型"""
    token: Token = Field(..., description="访问令牌信息")
    user: UserResponse = Field(..., description="用户信息")

    def model_dump(self, *args, **kwargs):
        """重写model_dump方法以处理datetime序列化"""
        d = super().model_dump(*args, **kwargs)
        if 'user' in d:
            if isinstance(d['user'].get('created_at'), datetime):
                d['user']['created_at'] = d['user']['created_at'].isoformat()
            if isinstance(d['user'].get('last_login'), datetime):
                d['user']['last_login'] = d['user']['last_login'].isoformat()
        return d

    class Config:
        json_schema_extra = {
            "example": {
                "token": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 3600
                },
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "username": "testuser",
                    "avatar_url": "http://example.com/avatar.jpg",
                    "is_active": True,
                    "created_at": "2024-01-01T00:00:00",
                    "last_login": "2024-01-02T10:30:00",
                    "login_count": 5
                }
            }
        }

class LoginResponse(BaseModel):
    """登录响应模型"""
    token: Token = Field(..., description="访问令牌信息")
    user: UserResponse = Field(..., description="用户信息")

    def model_dump(self, *args, **kwargs):
        """重写model_dump方法以处理datetime序列化"""
        d = super().model_dump(*args, **kwargs)
        if 'user' in d:
            if isinstance(d['user'].get('created_at'), datetime):
                d['user']['created_at'] = d['user']['created_at'].isoformat()
            if isinstance(d['user'].get('last_login'), datetime):
                d['user']['last_login'] = d['user']['last_login'].isoformat()
        return d

    class Config:
        json_schema_extra = {
            "example": {
                "token": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 3600
                },
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "username": "testuser",
                    "avatar_url": "http://example.com/avatar.jpg",
                    "is_active": True,
                    "created_at": "2024-01-01T00:00:00",
                    "last_login": "2024-01-02T10:30:00",
                    "login_count": 5
                }
            }
        }

# 错误响应模型
class ValidationErrorItem(BaseModel):
    """验证错误项模型"""
    field: str = Field(..., description="错误字段名")
    field_path: str = Field(..., description="错误字段完整路径")
    message: str = Field(..., description="错误信息")
    type: str = Field(..., description="错误类型")

class ValidationErrorResponse(BaseModel):
    """验证错误响应模型"""
    detail: str = Field(..., description="错误概述")
    type: str = Field(..., description="错误类型")
    errors: List[ValidationErrorItem] = Field(..., description="详细错误列表")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "输入数据验证失败",
                "type": "validation_error",
                "errors": [
                    {
                        "field": "username",
                        "field_path": "body.username",
                        "message": "用户名只能包含字母、数字、下划线和连字符",
                        "type": "value_error"
                    },
                    {
                        "field": "password",
                        "field_path": "body.password",
                        "message": "密码必须包含至少一个大写字母",
                        "type": "value_error"
                    }
                ]
            }
        }

class ErrorResponse(BaseModel):
    """通用错误响应模型"""
    detail: str = Field(..., description="错误信息")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "用户名或密码错误"
            }
        }

class RateLimitErrorResponse(BaseModel):
    """频率限制错误响应模型"""
    detail: str = Field(..., description="错误信息")
    retry_after: int = Field(..., description="需要等待的秒数")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "请求频率超过限制",
                "retry_after": 60
            }
        }

class AccountLockedErrorResponse(BaseModel):
    """账户锁定错误响应模型"""
    detail: str = Field(..., description="错误信息")
    locked_until: datetime = Field(..., description="锁定结束时间")
    remaining_time: int = Field(..., description="剩余锁定时间（秒）")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "账户已被锁定，请稍后再试",
                "locked_until": "2024-01-01T00:15:00",
                "remaining_time": 900
            }
        }

    def model_dump(self, *args, **kwargs):
        """重写model_dump方法以处理datetime序列化"""
        d = super().model_dump(*args, **kwargs)
        if isinstance(d.get('locked_until'), datetime):
            d['locked_until'] = d['locked_until'].isoformat()
        return d 