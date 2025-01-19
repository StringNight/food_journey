"""认证工具函数模块"""

from typing import Optional
from datetime import datetime, timedelta
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import os

from ..models.user import User
from ..utils.cache import CacheManager
from ..config.settings import settings

logger = logging.getLogger(__name__)

# 获取锁定时间配置
LOCKOUT_DURATION = int(os.getenv("LOCKOUT_DURATION", settings.LOCKOUT_DURATION))
IS_TESTING = os.getenv("TESTING", "false").lower() == "true"

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """根据用户名获取用户"""
    result = await db.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()

async def is_account_locked(cache: CacheManager, username: str) -> tuple[bool, int]:
    """检查账户是否被锁定
    
    Args:
        cache: 缓存管理器
        username: 用户名
        
    Returns:
        tuple[bool, int]: 返回一个元组，第一个元素表示账户是否被锁定，第二个元素表示剩余锁定时间（秒）
    """
    key = f"login_attempts:{username}"
    attempts = await cache.get(key)
    
    if attempts is None:
        return False, 0
        
    attempts = int(attempts)
    if attempts < settings.MAX_LOGIN_ATTEMPTS:
        return False, 0
        
    # 获取剩余锁定时间
    ttl = await cache.ttl(key)
    if ttl <= 0:  # 如果TTL已过期
        await cache.delete(key)  # 清除锁定状态
        return False, 0
        
    return True, ttl

async def increment_failed_attempts(cache: CacheManager, username: str) -> int:
    """增加登录失败次数
    
    Args:
        cache: 缓存管理器
        username: 用户名
        
    Returns:
        int: 当前失败次数
    """
    key = f"login_attempts:{username}"
    attempts = await cache.get(key)
    
    if attempts is None:
        attempts = 1
    else:
        attempts = int(attempts) + 1
        
    # 如果达到最大尝试次数，设置锁定时间
    if attempts >= settings.MAX_LOGIN_ATTEMPTS:
        # 将分钟转换为秒
        lockout_duration = LOCKOUT_DURATION * 60
        await cache.set(key, str(attempts), lockout_duration)
    else:
        # 未达到最大尝试次数，设置较短的过期时间
        await cache.set(key, str(attempts), 300)  # 5分钟
        
    return attempts

async def reset_failed_attempts(cache: CacheManager, username: str) -> None:
    """重置登录失败次数
    
    Args:
        cache: 缓存管理器
        username: 用户名
    """
    key = f"login_attempts:{username}"
    await cache.delete(key) 