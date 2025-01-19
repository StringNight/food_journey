"""
缓存服务模块

提供统一的缓存管理功能，支持多种缓存策略和自动过期
"""

from typing import Any, Dict, Optional, List, Union
from datetime import datetime, timedelta
import logging
from enum import Enum
from collections import OrderedDict
import sys
import json
import redis
import pickle
from functools import wraps

class CachePrefix(Enum):
    """缓存键前缀"""
    USER_PROFILE = "user_profile"
    RECIPE = "recipe"
    RATING = "rating"
    AI_RESPONSE = "ai_response"

class CacheStrategy(Enum):
    """缓存策略"""
    MEMORY = "memory"      # 简单内存缓存
    LRU = "lru"           # LRU缓存
    REDIS = "redis"       # Redis缓存
    MULTI = "multi"       # 多级缓存

class LRUCache:
    """LRU缓存实现"""
    
    def __init__(self, capacity: int):
        """初始化LRU缓存
        
        Args:
            capacity: 缓存容量（项数）
        """
        self.capacity = capacity
        self.cache = OrderedDict()
    
    def get(self, key: str) -> Optional[Dict]:
        """获取缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Dict]: 缓存的值
        """
        if key not in self.cache:
            return None
        
        # 移动到最新
        value = self.cache.pop(key)
        self.cache[key] = value
        return value
    
    def put(self, key: str, value: Dict):
        """添加缓存项
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        if key in self.cache:
            self.cache.pop(key)
        elif len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
        self.cache[key] = value

class RedisCache:
    """Redis缓存实现"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None
    ):
        """初始化Redis缓存
        
        Args:
            host: Redis主机
            port: Redis端口
            db: 数据库编号
            password: 密码
        """
        self.redis = None
        self.host = host
        self.port = port
        self.db = db
        self.password = password
    
    async def init(self):
        """初始化Redis连接"""
        self.redis = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=False
        )
    
    async def get(self, key: str) -> Optional[Dict]:
        """获取缓存项"""
        if not self.redis:
            return None
        
        try:
            data = self.redis.get(key)
            return pickle.loads(data) if data else None
        except Exception:
            return None
    
    async def set(
        self,
        key: str,
        value: Dict,
        expire: Optional[int] = None
    ):
        """设置缓存项"""
        if not self.redis:
            return
        
        try:
            data = pickle.dumps(value)
            if expire:
                self.redis.setex(key, expire, data)
            else:
                self.redis.set(key, data)
        except Exception:
            pass
    
    async def delete(self, key: str):
        """删除缓存项"""
        if self.redis:
            self.redis.delete(key)
    
    async def clear(self, pattern: str = "*"):
        """清除缓存"""
        if self.redis:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
    
    async def close(self):
        """关闭Redis连接"""
        if self.redis:
            self.redis.close()

class MultiLevelCache:
    """多级缓存实现"""
    
    def __init__(
        self,
        memory_cache: Union[dict, LRUCache],
        redis_cache: RedisCache
    ):
        """初始化多级缓存
        
        Args:
            memory_cache: 内存缓存
            redis_cache: Redis缓存
        """
        self.memory_cache = memory_cache
        self.redis_cache = redis_cache
    
    async def get(self, key: str) -> Optional[Dict]:
        """获取缓存项"""
        # 先从内存缓存获取
        if isinstance(self.memory_cache, LRUCache):
            value = self.memory_cache.get(key)
        else:
            value = self.memory_cache.get(key)
        
        if value:
            return value.get("data")
        
        # 从Redis获取
        value = await self.redis_cache.get(key)
        if value:
            # 更新内存缓存
            cache_data = {
                "data": value,
                "expiry": None,
                "created_at": datetime.now()
            }
            if isinstance(self.memory_cache, LRUCache):
                self.memory_cache.put(key, cache_data)
            else:
                self.memory_cache[key] = cache_data
        
        return value
    
    async def set(
        self,
        key: str,
        value: Dict,
        expire: Optional[int] = None
    ):
        """设置缓存项"""
        # 更新内存缓存
        expiry = (
            datetime.now() + timedelta(seconds=expire)
            if expire else None
        )
        cache_data = {
            "data": value,
            "expiry": expiry,
            "created_at": datetime.now()
        }
        
        if isinstance(self.memory_cache, LRUCache):
            self.memory_cache.put(key, cache_data)
        else:
            self.memory_cache[key] = cache_data
        
        # 更新Redis缓存
        await self.redis_cache.set(key, value, expire)
    
    async def delete(self, key: str):
        """删除缓存项"""
        # 删除内存缓存
        if isinstance(self.memory_cache, LRUCache):
            if key in self.memory_cache.cache:
                self.memory_cache.cache.pop(key)
        else:
            if key in self.memory_cache:
                del self.memory_cache[key]
        
        # 删除Redis缓存
        await self.redis_cache.delete(key)

class CacheService:
    """缓存服务类"""
    
    def __init__(
        self,
        strategy: CacheStrategy = CacheStrategy.MULTI,
        capacity: int = 1000,
        max_memory_mb: int = 100,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None
    ):
        """初始化缓存服务
        
        Args:
            strategy: 缓存策略
            capacity: 缓存容量（项数）
            max_memory_mb: 最大内存使用量（MB）
            redis_host: Redis主机
            redis_port: Redis端口
            redis_db: Redis数据库编号
            redis_password: Redis密码
        """
        self.strategy = strategy
        self.max_memory = max_memory_mb * 1024 * 1024
        self.logger = logging.getLogger(__name__)
        
        # 初始化缓存
        if strategy == CacheStrategy.LRU:
            self.cache = LRUCache(capacity)
        elif strategy == CacheStrategy.REDIS:
            self.cache = RedisCache(
                redis_host,
                redis_port,
                redis_db,
                redis_password
            )
        elif strategy == CacheStrategy.MULTI:
            memory_cache = LRUCache(capacity)
            redis_cache = RedisCache(
                redis_host,
                redis_port,
                redis_db,
                redis_password
            )
            self.cache = MultiLevelCache(memory_cache, redis_cache)
        else:
            self.cache = {}
        
        # 缓存统计
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    async def init(self):
        """初始化缓存服务"""
        if isinstance(self.cache, RedisCache):
            await self.cache.init()
        elif isinstance(self.cache, MultiLevelCache):
            await self.cache.redis_cache.init()
    
    def _build_key(self, prefix: CachePrefix, key: str) -> str:
        """构建缓存键"""
        return f"{prefix.value}:{key}"
    
    def _check_memory_usage(self) -> bool:
        """检查内存使用量"""
        try:
            if isinstance(self.cache, (RedisCache, MultiLevelCache)):
                return True
            
            cache_size = sys.getsizeof(json.dumps(self.cache))
            return cache_size <= self.max_memory
        except Exception as e:
            self.logger.error(f"检查内存使用量失败: {str(e)}")
            return True
    
    async def _evict_expired(self) -> List[str]:
        """清除过期的缓存项"""
        now = datetime.now()
        evicted_keys = []
        
        if isinstance(self.cache, LRUCache):
            cache_items = list(self.cache.cache.items())
        elif isinstance(self.cache, dict):
            cache_items = list(self.cache.items())
        else:
            return []
        
        for key, value in cache_items:
            if (
                "expiry" in value and 
                value["expiry"] and 
                now > value["expiry"]
            ):
                prefix = CachePrefix(key.split(":")[0])
                await self.delete(prefix, key.split(":")[1])
                evicted_keys.append(key)
                self.stats["evictions"] += 1
        
        return evicted_keys
    
    async def get(
        self,
        prefix: CachePrefix,
        key: str
    ) -> Optional[Dict]:
        """获取缓存值"""
        try:
            cache_key = self._build_key(prefix, key)
            
            if isinstance(self.cache, (RedisCache, MultiLevelCache)):
                cached_data = await self.cache.get(cache_key)
            elif isinstance(self.cache, LRUCache):
                cached_data = self.cache.get(cache_key)
            else:
                cached_data = self.cache.get(cache_key)
            
            if not cached_data:
                self.stats["misses"] += 1
                return None
            
            # 检查是否过期
            if isinstance(cached_data, dict) and "expiry" in cached_data:
                if (
                    cached_data["expiry"] and 
                    datetime.now() > cached_data["expiry"]
                ):
                    await self.delete(prefix, key)
                    self.stats["evictions"] += 1
                    return None
                cached_data = cached_data.get("data")
            
            self.stats["hits"] += 1
            return cached_data
            
        except Exception as e:
            self.logger.error(f"获取缓存失败: {str(e)}")
            return None
    
    async def set(
        self,
        prefix: CachePrefix,
        key: str,
        value: Dict,
        expire_in: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        try:
            # 检查内存使用量
            if not self._check_memory_usage():
                # 尝试清理过期项
                await self._evict_expired()
                # 再次检查
                if not self._check_memory_usage():
                    self.logger.warning("缓存内存使用量超过限制")
                    return False
            
            cache_key = self._build_key(prefix, key)
            
            if isinstance(self.cache, (RedisCache, MultiLevelCache)):
                await self.cache.set(cache_key, value, expire_in)
            else:
                # 计算过期时间
                expiry = (
                    datetime.now() + timedelta(seconds=expire_in)
                    if expire_in else None
                )
                
                # 存储数据
                cache_data = {
                    "data": value,
                    "expiry": expiry,
                    "created_at": datetime.now()
                }
                
                if isinstance(self.cache, LRUCache):
                    self.cache.put(cache_key, cache_data)
                else:
                    self.cache[cache_key] = cache_data
            
            return True
            
        except Exception as e:
            self.logger.error(f"设置缓存失败: {str(e)}")
            return False
    
    async def delete(self, prefix: CachePrefix, key: str) -> bool:
        """删除缓存"""
        try:
            cache_key = self._build_key(prefix, key)
            
            if isinstance(self.cache, (RedisCache, MultiLevelCache)):
                await self.cache.delete(cache_key)
            elif isinstance(self.cache, LRUCache):
                if cache_key in self.cache.cache:
                    self.cache.cache.pop(cache_key)
            else:
                if cache_key in self.cache:
                    del self.cache[cache_key]
            
            return True
            
        except Exception as e:
            self.logger.error(f"删除缓存失败: {str(e)}")
            return False
    
    async def clear(self, prefix: Optional[CachePrefix] = None) -> bool:
        """清除缓存"""
        try:
            if isinstance(self.cache, RedisCache):
                pattern = f"{prefix.value}:*" if prefix else "*"
                await self.cache.clear(pattern)
            elif isinstance(self.cache, MultiLevelCache):
                pattern = f"{prefix.value}:*" if prefix else "*"
                await self.cache.redis_cache.clear(pattern)
                # 清除内存缓存
                if isinstance(self.cache.memory_cache, LRUCache):
                    self.cache.memory_cache.cache.clear()
                else:
                    self.cache.memory_cache.clear()
            else:
                if prefix:
                    # 清除指定前缀的缓存
                    prefix_str = f"{prefix.value}:"
                    if isinstance(self.cache, LRUCache):
                        keys = [
                            k for k in self.cache.cache.keys()
                            if k.startswith(prefix_str)
                        ]
                        for k in keys:
                            self.cache.cache.pop(k)
                    else:
                        keys = [
                            k for k in self.cache.keys()
                            if k.startswith(prefix_str)
                        ]
                        for k in keys:
                            del self.cache[k]
                else:
                    # 清除所有缓存
                    if isinstance(self.cache, LRUCache):
                        self.cache.cache.clear()
                    else:
                        self.cache.clear()
                    self.stats = {"hits": 0, "misses": 0, "evictions": 0}
            
            return True
            
        except Exception as e:
            self.logger.error(f"清除缓存失败: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            if isinstance(self.cache, RedisCache):
                # Redis缓存统计
                return {
                    "strategy": self.strategy.value,
                    "hits": self.stats["hits"],
                    "misses": self.stats["misses"],
                    "evictions": self.stats["evictions"]
                }
            elif isinstance(self.cache, MultiLevelCache):
                # 多级缓存统计
                memory_size = (
                    len(self.cache.memory_cache.cache)
                    if isinstance(self.cache.memory_cache, LRUCache)
                    else len(self.cache.memory_cache)
                )
                return {
                    "strategy": self.strategy.value,
                    "hits": self.stats["hits"],
                    "misses": self.stats["misses"],
                    "evictions": self.stats["evictions"],
                    "memory_items": memory_size
                }
            else:
                # 内存缓存统计
                if isinstance(self.cache, LRUCache):
                    total_items = len(self.cache.cache)
                    cache_items = self.cache.cache
                else:
                    total_items = len(self.cache)
                    cache_items = self.cache
                
                expired_items = sum(
                    1 for item in cache_items.values()
                    if item.get("expiry") and datetime.now() > item["expiry"]
                )
                
                # 按前缀统计
                prefix_stats = {}
                for key in cache_items:
                    prefix = key.split(":")[0]
                    prefix_stats[prefix] = prefix_stats.get(prefix, 0) + 1
                
                # 计算命中率
                total_requests = self.stats["hits"] + self.stats["misses"]
                hit_rate = (
                    self.stats["hits"] / total_requests * 100 
                    if total_requests > 0 else 0
                )
                
                return {
                    "total_items": total_items,
                    "expired_items": expired_items,
                    "prefix_stats": prefix_stats,
                    "strategy": self.strategy.value,
                    "hits": self.stats["hits"],
                    "misses": self.stats["misses"],
                    "evictions": self.stats["evictions"],
                    "hit_rate": f"{hit_rate:.2f}%",
                    "memory_usage": sys.getsizeof(json.dumps(cache_items))
                }
            
        except Exception as e:
            self.logger.error(f"获取缓存统计失败: {str(e)}")
            return {}
    
    async def close(self):
        """关闭缓存服务"""
        if isinstance(self.cache, RedisCache):
            await self.cache.close()
        elif isinstance(self.cache, MultiLevelCache):
            await self.cache.redis_cache.close() 