"""缓存管理模块"""

from typing import Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """缓存管理器类"""
    
    def __init__(self):
        """初始化缓存管理器"""
        self._cache = {}
        
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self._cache:
            return None
            
        value, expiry = self._cache[key]
        if expiry and datetime.now() > expiry:
            del self._cache[key]
            return None
            
        return value
        
    async def set(self, key: str, value: Any, expire_seconds: Optional[int] = None):
        """设置缓存值"""
        expiry = None
        if expire_seconds:
            expiry = datetime.now() + timedelta(seconds=expire_seconds)
            
        self._cache[key] = (value, expiry)
        
    async def delete(self, key: str):
        """删除缓存值"""
        if key in self._cache:
            del self._cache[key]
            
    async def increment(self, key: str, amount: int = 1) -> int:
        """增加计数器值"""
        value = await self.get(key) or 0
        value += amount
        await self.set(key, value)
        return value
        
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return await self.get(key) is not None
        
    async def ttl(self, key: str) -> int:
        """获取键的剩余生存时间（秒）
        
        Args:
            key: 缓存键
            
        Returns:
            int: 剩余生存时间（秒），如果键不存在或已过期则返回-1
        """
        if key not in self._cache:
            return -1
            
        value, expiry = self._cache[key]
        if not expiry:
            return -1
            
        remaining = (expiry - datetime.now()).total_seconds()
        if remaining <= 0:
            del self._cache[key]
            return -1
            
        return int(remaining)
        
    async def expire(self, key: str, seconds: int):
        """设置键的过期时间
        
        Args:
            key: 缓存键
            seconds: 过期时间（秒）
        """
        if key in self._cache:
            value, _ = self._cache[key]
            expiry = datetime.now() + timedelta(seconds=seconds)
            self._cache[key] = (value, expiry)

# 创建全局缓存管理器实例
_cache_manager = CacheManager()

def get_cache_manager() -> CacheManager:
    """获取缓存管理器实例"""
    return _cache_manager 