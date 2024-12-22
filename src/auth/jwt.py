from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

from src.database import get_db
from src.models.user import User

# 加载环境变量
load_dotenv()

# 配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-here")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def create_refresh_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not hasattr(current_user, 'is_active') or not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已被禁用"
        )
    return current_user

def create_tokens_for_user(user: User) -> Dict[str, str]:
    access_token_data = {
        "sub": user.username,
        "type": "access"
    }
    refresh_token_data = {
        "sub": user.username,
        "type": "refresh"
    }
    
    return {
        "access_token": create_access_token(access_token_data),
        "refresh_token": create_refresh_token(refresh_token_data),
        "token_type": "bearer"
    }

async def refresh_access_token(refresh_token: str, db: Session) -> Dict[str, str]:
    """刷新访问令牌
    
    使用刷新令牌获取新的访问令牌
    
    Args:
        refresh_token: 刷新令牌
        db: 数据库会话
        
    Returns:
        Dict: 新的令牌对
        
    Raises:
        HTTPException: 当刷新令牌无效时抛出
    """
    try:
        payload = verify_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
            
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在"
            )
            
        return create_tokens_for_user(user)
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )

def revoke_token(token: str):
    """撤销令牌
    
    将令牌加入黑名单（待实现）
    
    Args:
        token: 要撤销的令牌
    """
    # TODO: 实现令牌黑名单机制
    pass

def is_token_revoked(token: str) -> bool:
    """检查令牌是否已撤销
    
    检查令牌是否在黑名单中（待实现）
    
    Args:
        token: 要检查的令牌
        
    Returns:
        bool: 令牌是否已撤销
    """
    # TODO: 实现令牌黑名单检查
    return False 