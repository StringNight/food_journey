"""JWT认证模块

提供JWT令牌的创建、验证和用户认证功能
"""

from datetime import datetime, timedelta, UTC
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models.user import User
from ..config.settings import settings
import logging

# OAuth2密码承载令牌URL
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=True
)

def create_access_token(data: dict) -> tuple[str, int]:
    """创建访问令牌
    
    Args:
        data: 要编码到令牌中的数据
        
    Returns:
        tuple[str, int]: 包含JWT访问令牌和过期时间（秒）的元组
    """
    to_encode = data.copy()
    # 设置令牌过期时间
    expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # 使用密钥创建JWT令牌
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前认证用户
    
    Args:
        token: JWT令牌
        db: 数据库会话
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 如果令牌无效或用户不存在
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 解码JWT令牌
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # 从数据库获取用户
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    return user

async def optional_current_user(
    token: Optional[str] = Depends(OAuth2PasswordBearer(
        tokenUrl="/api/v1/auth/login",
        auto_error=False
    )),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（可选）
    
    与get_current_user不同，此函数在未提供令牌时不会引发异常
    
    Args:
        token: JWT令牌（可选）
        db: 数据库会话
        
    Returns:
        Optional[User]: 当前用户对象，如果未提供有效令牌则返回None
    """
    if not token:
        return None
        
    try:
        # 解码JWT令牌
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
            
        # 从数据库获取用户
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user is None or not user.is_active:
            return None
            
        return user
        
    except JWTError:
        return None 