"""
缓存预热服务模块

提供缓存预热、维护和优化功能
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
import asyncio
from .database_service import DatabaseService
from .cache_service import CacheService, CachePrefix

class WarmupService:
    def __init__(
        self,
        db_service: DatabaseService,
        cache_service: CacheService
    ):
        """初始化缓存预热服务
        
        Args:
            db_service: 数据库服务实例
            cache_service: 缓存服务实例
        """
        self.db_service = db_service
        self.cache_service = cache_service
        self.logger = logging.getLogger(__name__)
        
        # 预热配置
        self.config = {
            "recipes": {
                "batch_size": 100,  # 每批处理的数量
                "max_age_days": 30,  # 最大数据年龄（天）
                "min_rating": 4.0    # 最低评分
            },
            "users": {
                "batch_size": 100,
                "active_days": 7     # 活跃用户天数
            }
        }
    
    async def warmup_all(self):
        """预热所有缓存"""
        try:
            # 预热热门菜谱
            await self.warmup_popular_recipes()
            # 预热活跃用户
            await self.warmup_active_users()
            # 预热系统配置
            await self.warmup_system_config()
            
            self.logger.info("所有缓存预热完成")
            
        except Exception as e:
            self.logger.error(f"缓存预热失败: {str(e)}")
            raise
    
    async def warmup_popular_recipes(self):
        """预热热门菜谱缓存"""
        try:
            config = self.config["recipes"]
            
            # 查询热门菜谱
            query = """
                SELECT r.*, 
                    COALESCE(AVG(rt.rating), 0) as average_rating,
                    COUNT(rt.id) as rating_count
                FROM recipes r
                LEFT JOIN ratings rt ON r.id = rt.recipe_id
                WHERE r.created_at >= NOW() - INTERVAL '%s days'
                GROUP BY r.id
                HAVING COALESCE(AVG(rt.rating), 0) >= %s
                ORDER BY rating_count DESC, average_rating DESC
            """
            recipes = await self.db_service.fetch(
                query,
                config["max_age_days"],
                config["min_rating"]
            )
            
            # 分批处理
            for i in range(0, len(recipes), config["batch_size"]):
                batch = recipes[i:i + config["batch_size"]]
                await asyncio.gather(*[
                    self.cache_service.set(
                        CachePrefix.RECIPE,
                        recipe["id"],
                        recipe
                    )
                    for recipe in batch
                ])
            
            self.logger.info(f"预热了 {len(recipes)} 个热门菜谱")
            
        except Exception as e:
            self.logger.error(f"预热热门菜谱失败: {str(e)}")
            raise
    
    async def warmup_active_users(self):
        """预热活跃用户缓存"""
        try:
            config = self.config["users"]
            
            # 查询活跃用户
            query = """
                SELECT u.*, 
                    COUNT(DISTINCT r.id) as recipe_count,
                    COUNT(DISTINCT rt.id) as rating_count
                FROM users u
                LEFT JOIN recipes r ON r.user_id = u.id
                LEFT JOIN ratings rt ON rt.user_id = u.id
                WHERE u.last_login >= NOW() - INTERVAL '%s days'
                GROUP BY u.id
                ORDER BY recipe_count DESC, rating_count DESC
            """
            users = await self.db_service.fetch(
                query,
                config["active_days"]
            )
            
            # 分批处理
            for i in range(0, len(users), config["batch_size"]):
                batch = users[i:i + config["batch_size"]]
                await asyncio.gather(*[
                    self.cache_service.set(
                        CachePrefix.USER_PROFILE,
                        user["id"],
                        user
                    )
                    for user in batch
                ])
            
            self.logger.info(f"预热了 {len(users)} 个活跃用户")
            
        except Exception as e:
            self.logger.error(f"预热活跃用户失败: {str(e)}")
            raise
    
    async def warmup_system_config(self):
        """预热系统配置缓存"""
        try:
            # 查询系统配置
            query = "SELECT * FROM system_config"
            configs = await self.db_service.fetch(query)
            
            # 缓存配置
            for config in configs:
                await self.cache_service.set(
                    CachePrefix.SYSTEM_CONFIG,
                    config["key"],
                    config,
                    expire_in=3600  # 1小时过期
                )
            
            self.logger.info(f"预热了 {len(configs)} 个系统配置")
            
        except Exception as e:
            self.logger.error(f"预热系统配置失败: {str(e)}")
            raise
    
    async def warmup_recipe(self, recipe_id: str) -> bool:
        """预热单个菜谱缓存
        
        Args:
            recipe_id: 菜谱ID
            
        Returns:
            bool: 是否成功
        """
        try:
            # 查询菜谱详情
            query = """
                SELECT r.*, 
                    COALESCE(AVG(rt.rating), 0) as average_rating,
                    COUNT(rt.id) as rating_count
                FROM recipes r
                LEFT JOIN ratings rt ON r.id = rt.recipe_id
                WHERE r.id = $1
                GROUP BY r.id
            """
            recipe = await self.db_service.fetch_one(query, recipe_id)
            
            if not recipe:
                return False
            
            # 更新缓存
            await self.cache_service.set(
                CachePrefix.RECIPE,
                recipe_id,
                recipe
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"预热菜谱失败: {str(e)}")
            return False
    
    async def warmup_user(self, user_id: str) -> bool:
        """预热单个用户缓存
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否成功
        """
        try:
            # 查询用户详情
            query = """
                SELECT u.*, 
                    COUNT(DISTINCT r.id) as recipe_count,
                    COUNT(DISTINCT rt.id) as rating_count
                FROM users u
                LEFT JOIN recipes r ON r.user_id = u.id
                LEFT JOIN ratings rt ON rt.user_id = u.id
                WHERE u.id = $1
                GROUP BY u.id
            """
            user = await self.db_service.fetch_one(query, user_id)
            
            if not user:
                return False
            
            # 更新缓存
            await self.cache_service.set(
                CachePrefix.USER_PROFILE,
                user_id,
                user
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"预热用户失败: {str(e)}")
            return False
    
    def update_config(self, new_config: Dict[str, Any]):
        """更新预热配置
        
        Args:
            new_config: 新的配置
        """
        self.config.update(new_config)
        self.logger.info("预热配置已更新")
    
    async def get_warmup_stats(self) -> Dict[str, Any]:
        """获取预热统计信息"""
        try:
            # 获取缓存统计
            cache_stats = self.cache_service.get_stats()
            
            # 计算预热率
            total_recipes = await self.db_service.fetch_one(
                "SELECT COUNT(*) as count FROM recipes"
            )
            total_users = await self.db_service.fetch_one(
                "SELECT COUNT(*) as count FROM users"
            )
            
            recipe_cache_count = cache_stats.get("prefix_stats", {}).get(
                CachePrefix.RECIPE.value, 0
            )
            user_cache_count = cache_stats.get("prefix_stats", {}).get(
                CachePrefix.USER_PROFILE.value, 0
            )
            
            return {
                "recipes": {
                    "total": total_recipes["count"],
                    "cached": recipe_cache_count,
                    "warmup_rate": (
                        f"{recipe_cache_count/total_recipes['count']*100:.2f}%"
                        if total_recipes["count"] > 0 else "0.00%"
                    )
                },
                "users": {
                    "total": total_users["count"],
                    "cached": user_cache_count,
                    "warmup_rate": (
                        f"{user_cache_count/total_users['count']*100:.2f}%"
                        if total_users["count"] > 0 else "0.00%"
                    )
                },
                "cache_stats": cache_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"获取预热统计失败: {str(e)}")
            return {} 