import redis
from functools import lru_cache
import json
import logging
from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timedelta

class CachePrefix:
    """缓存键前缀常量
    
    定义所有缓存键的前缀，便于管理和维护
    """
    USER = "user"  # 用户相关缓存
    RECIPE = "recipe"  # 菜谱相关缓存
    PROFILE = "profile"  # 用户画像相关缓存
    TOKEN = "token"  # 认证令牌相关缓存
    STATS = "stats"  # 统计数据相关缓存

class CacheManager:
    """缓存管理器
    
    提供Redis缓存的管理功能，支持自动序列化和反序列化，
    以及优雅的降级处理
    """
    
    def __init__(self, redis_host='localhost', redis_port=6379):
        """初始化缓存管理器
        
        Args:
            redis_host: Redis主机地址
            redis_port: Redis端口号
        """
        self.memory_cache = {}  # 内存缓存
        self.memory_cache_expiry = {}  # 内存缓存过期时间
        self.use_redis = False  # 默认不使用 Redis
        self.redis_client = None
        
        # 尝试连接 Redis
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                socket_connect_timeout=1  # 1秒连接超时
            )
            # 测试连接
            self.redis_client.ping()
            self.use_redis = True
            logging.info("Redis连接成功，将使用Redis缓存")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logging.warning(f"Redis连接失败，将使用内存缓存: {e}")
            self.redis_client = None
            self.use_redis = False
        except Exception as e:
            logging.warning(f"Redis初始化出错，将使用内存缓存: {e}")
            self.redis_client = None
            self.use_redis = False
    
    def _get_key(self, prefix: str, key: str) -> str:
        """生成缓存键
        
        Args:
            prefix: 键前缀
            key: 键名
            
        Returns:
            str: 完整的缓存键
        """
        return f"{prefix}:{key}"
    
    def _cleanup_expired_memory_cache(self):
        """清理过期的内存缓存
        
        删除所有已过期的内存缓存项
        """
        now = datetime.now()
        expired_keys = [
            k for k, v in self.memory_cache_expiry.items()
            if now > v
        ]
        for k in expired_keys:
            del self.memory_cache[k]
            del self.memory_cache_expiry[k]
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值
        
        Args:
            key: 缓存键
            default: 默认值
            
        Returns:
            Any: 缓存值或默认值
        """
        # 清理过期缓存
        self._cleanup_expired_memory_cache()
        
        # 优先尝试Redis
        if self.use_redis:
            try:
                value = self.redis_client.get(key)
                if value is not None:
                    return json.loads(value)
            except Exception as e:
                logging.error(f"Redis获取失败: {e}")
        
        # 降级到内存缓存
        return self.memory_cache.get(key, default)
    
    def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒或timedelta对象）
            
        Returns:
            bool: 是否设置成功
        """
        # 序列化值
        try:
            serialized_value = json.dumps(value)
        except Exception as e:
            logging.error(f"值序列化失败: {e}")
            return False
        
        # 计算过期时间
        if isinstance(expire, timedelta):
            expire_seconds = int(expire.total_seconds())
        else:
            expire_seconds = expire
        
        # 优先尝试Redis
        if self.use_redis:
            try:
                if expire_seconds is not None:
                    self.redis_client.setex(key, expire_seconds, serialized_value)
                else:
                    self.redis_client.set(key, serialized_value)
                return True
            except Exception as e:
                logging.error(f"Redis设置失败: {e}")
        
        # 降级到内存缓存
        self.memory_cache[key] = value
        if expire_seconds is not None:
            self.memory_cache_expiry[key] = datetime.now() + timedelta(seconds=expire_seconds)
        return True
    
    def delete(self, key: str) -> bool:
        """删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        success = True
        
        # 尝试从Redis删除
        if self.use_redis:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logging.error(f"Redis删除失败: {e}")
                success = False
        
        # 从内存缓存删除
        self.memory_cache.pop(key, None)
        self.memory_cache_expiry.pop(key, None)
        
        return success
    
    def exists(self, key: str) -> bool:
        """检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 缓存是否存在
        """
        # 清理过期缓存
        self._cleanup_expired_memory_cache()
        
        # 优先检查Redis
        if self.use_redis:
            try:
                return bool(self.redis_client.exists(key))
            except Exception as e:
                logging.error(f"Redis检查失败: {e}")
        
        # 降级到内存缓存
        return key in self.memory_cache
    
    def clear(self) -> bool:
        """清空所有缓存
        
        Returns:
            bool: 是否清空成功
        """
        success = True
        
        # 尝试清空Redis
        if self.use_redis:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                logging.error(f"Redis清空失败: {e}")
                success = False
        
        # 清空内存缓存
        self.memory_cache.clear()
        self.memory_cache_expiry.clear()
        
        return success
    
    def get_many(self, keys: List[str], default: Any = None) -> Dict[str, Any]:
        """批量获取缓存值
        
        Args:
            keys: 缓存键列表
            default: 默认值
            
        Returns:
            Dict[str, Any]: 键值对字典
        """
        result = {}
        
        # 清理过期缓存
        self._cleanup_expired_memory_cache()
        
        # 优先尝试Redis
        if self.use_redis:
            try:
                values = self.redis_client.mget(keys)
                for key, value in zip(keys, values):
                    if value is not None:
                        result[key] = json.loads(value)
                    else:
                        result[key] = default
                return result
            except Exception as e:
                logging.error(f"Redis批量获取失败: {e}")
        
        # 降级到内存缓存
        for key in keys:
            result[key] = self.memory_cache.get(key, default)
        
        return result
    
    def set_many(self, mapping: Dict[str, Any], expire: Optional[Union[int, timedelta]] = None) -> bool:
        """批量设置缓存值
        
        Args:
            mapping: 键值对字典
            expire: 过期时间（秒或timedelta对象）
            
        Returns:
            bool: 是否全部设置成功
        """
        success = True
        
        # 计算过期时间
        if isinstance(expire, timedelta):
            expire_seconds = int(expire.total_seconds())
        else:
            expire_seconds = expire
        
        # 序列化值
        try:
            serialized_mapping = {
                k: json.dumps(v) for k, v in mapping.items()
            }
        except Exception as e:
            logging.error(f"值序列化失败: {e}")
            return False
        
        # 优先尝试Redis
        if self.use_redis:
            try:
                pipeline = self.redis_client.pipeline()
                for key, value in serialized_mapping.items():
                    if expire_seconds is not None:
                        pipeline.setex(key, expire_seconds, value)
                    else:
                        pipeline.set(key, value)
                pipeline.execute()
            except Exception as e:
                logging.error(f"Redis批量设置失败: {e}")
                success = False
        
        # 降级到内存缓存
        for key, value in mapping.items():
            self.memory_cache[key] = value
            if expire_seconds is not None:
                self.memory_cache_expiry[key] = datetime.now() + timedelta(seconds=expire_seconds)
        
        return success
    
    def close(self):
        """关闭缓存管理器
        
        关闭Redis连接并清理资源
        """
        if self.redis_client:
            try:
                self.redis_client.close()
            except Exception as e:
                logging.error(f"Redis关闭失败: {e}")
        
        self.memory_cache.clear()
        self.memory_cache_expiry.clear()
    
    def clear_prefix(self, prefix: str) -> bool:
        """清除指定前缀的所有缓存
        
        Args:
            prefix: 缓存键前缀
            
        Returns:
            bool: 是否清除成功
        """
        success = True
        
        # 优先尝试Redis
        if self.use_redis:
            try:
                pattern = f"{prefix}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                logging.error(f"Redis清除前缀失败: {e}")
                success = False
        
        # 清除内存缓存
        keys_to_delete = [
            k for k in self.memory_cache.keys()
            if k.startswith(prefix)
        ]
        for k in keys_to_delete:
            self.memory_cache.pop(k, None)
            self.memory_cache_expiry.pop(k, None)
        
        return success
    
    @lru_cache(maxsize=1000)
    def get_popular_recipes(self) -> List[Dict]:
        """获取热门菜谱（使用Python内置的LRU缓存）
        
        Returns:
            List[Dict]: 热门菜谱列表
        """
        key = f"{CachePrefix.RECIPE}:popular"
        
        # 尝试从缓存获取
        recipes = self.get(key)
        if recipes is not None:
            return recipes
        
        # TODO: 从数据库获取热门菜谱
        recipes = []
        
        # 缓存结果
        self.set(key, recipes, expire=timedelta(hours=1))
        return recipes
    
    def invalidate_popular_recipes(self):
        """清除热门菜谱缓存"""
        self.get_popular_recipes.cache_clear()
        self.delete(f"{CachePrefix.RECIPE}:popular")
    
    def cache_user_token(self, user_id: str, token: str, expire: timedelta):
        """缓存用户令牌
        
        Args:
            user_id: 用户ID
            token: 认证令牌
            expire: 过期时间
        """
        key = f"{CachePrefix.TOKEN}:{user_id}"
        self.set(key, token, expire=expire)
    
    def get_user_token(self, user_id: str) -> Optional[str]:
        """获取用户令牌
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[str]: 认证令牌
        """
        key = f"{CachePrefix.TOKEN}:{user_id}"
        return self.get(key)
    
    def invalidate_user_token(self, user_id: str):
        """使用户令牌失效
        
        Args:
            user_id: 用户ID
        """
        key = f"{CachePrefix.TOKEN}:{user_id}"
        self.delete(key)
    
    def cache_user_profile(self, user_id: str, profile: Dict):
        """缓存用户画像
        
        Args:
            user_id: 用户ID
            profile: 用户画像数据
        """
        key = f"{CachePrefix.PROFILE}:{user_id}"
        self.set(key, profile, expire=timedelta(hours=24))
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """获取用户画像
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[Dict]: 用户画像数据
        """
        key = f"{CachePrefix.PROFILE}:{user_id}"
        return self.get(key)
    
    def invalidate_user_profile(self, user_id: str):
        """使用户画像缓存失效
        
        Args:
            user_id: 用户ID
        """
        key = f"{CachePrefix.PROFILE}:{user_id}"
        self.delete(key)
    
    def increment_recipe_views(self, recipe_id: str) -> Optional[int]:
        """增加菜谱浏览次数
        
        Args:
            recipe_id: 菜谱ID
            
        Returns:
            Optional[int]: 更新后的浏览次数
        """
        key = f"{CachePrefix.STATS}:recipe_views:{recipe_id}"
        
        if self.use_redis:
            try:
                return self.redis_client.incr(key)
            except Exception as e:
                logging.error(f"Redis增加浏览次数失败: {e}")
        
        # 降级到内存缓存
        current_views = self.get(key, 0)
        new_views = current_views + 1
        self.set(key, new_views)
        return new_views
    
    def get_recipe_views(self, recipe_id: str) -> int:
        """获取菜谱浏览次数
        
        Args:
            recipe_id: 菜谱ID
            
        Returns:
            int: 浏览次数
        """
        key = f"{CachePrefix.STATS}:recipe_views:{recipe_id}"
        return self.get(key, 0)
    
    def cache_recipe_search_results(self, query: str, results: List[Dict]):
        """缓存菜谱搜索结果
        
        Args:
            query: 搜索查询
            results: 搜索结果
        """
        key = f"{CachePrefix.RECIPE}:search:{query}"
        self.set(key, results, expire=timedelta(minutes=30))
    
    def get_recipe_search_results(self, query: str) -> Optional[List[Dict]]:
        """获取缓存的菜谱搜索结果
        
        Args:
            query: 搜索查询
            
        Returns:
            Optional[List[Dict]]: 搜索结果
        """
        key = f"{CachePrefix.RECIPE}:search:{query}"
        return self.get(key)
 