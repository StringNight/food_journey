"""
索引管理服务模块

提供数据库索引的创建、维护和优化功能
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime
from .database_service import DatabaseService

class IndexService:
    def __init__(self, db_service: DatabaseService):
        """初始化索引服务
        
        Args:
            db_service: 数据库服务实例
        """
        self.db_service = db_service
        self.logger = logging.getLogger(__name__)
    
    async def create_indexes(self):
        """创建所有必要的索引"""
        try:
            # 菜谱表索引
            await self._create_recipe_indexes()
            # 评分表索引
            await self._create_rating_indexes()
            # 用户表索引
            await self._create_user_indexes()
            
            self.logger.info("所有索引创建成功")
            
        except Exception as e:
            self.logger.error(f"创建索引失败: {str(e)}")
            raise
    
    async def _create_recipe_indexes(self):
        """创建菜谱表索引"""
        indexes = [
            # 主键索引（自动创建）
            """
            CREATE INDEX IF NOT EXISTS idx_recipes_cuisine_type 
            ON recipes (cuisine_type)
            """,
            # 复合索引：烹饪时间和难度
            """
            CREATE INDEX IF NOT EXISTS idx_recipes_cooking_time_difficulty 
            ON recipes (cooking_time, difficulty)
            """,
            # 平均评分索引
            """
            CREATE INDEX IF NOT EXISTS idx_recipes_average_rating 
            ON recipes (average_rating DESC)
            """,
            # 创建时间索引
            """
            CREATE INDEX IF NOT EXISTS idx_recipes_created_at 
            ON recipes (created_at DESC)
            """
        ]
        
        for index in indexes:
            await self.db_service.execute(index)
    
    async def _create_rating_indexes(self):
        """创建评分表索引"""
        indexes = [
            # 菜谱ID索引
            """
            CREATE INDEX IF NOT EXISTS idx_ratings_recipe_id 
            ON ratings (recipe_id)
            """,
            # 评分索引
            """
            CREATE INDEX IF NOT EXISTS idx_ratings_rating 
            ON ratings (rating DESC)
            """,
            # 创建时间索引
            """
            CREATE INDEX IF NOT EXISTS idx_ratings_created_at 
            ON ratings (created_at DESC)
            """
        ]
        
        for index in indexes:
            await self.db_service.execute(index)
    
    async def _create_user_indexes(self):
        """创建用户表索引"""
        indexes = [
            # 用户名索引
            """
            CREATE INDEX IF NOT EXISTS idx_users_username 
            ON users (username)
            """,
            # 最后登录时间索引
            """
            CREATE INDEX IF NOT EXISTS idx_users_last_login 
            ON users (last_login DESC)
            """,
        ]
        
        for index in indexes:
            await self.db_service.execute(index)
    
    async def analyze_table_stats(self) -> Dict:
        """分析表统计信息"""
        try:
            # 获取表大小
            query = """
                SELECT 
                    relname as table_name,
                    pg_size_pretty(pg_total_relation_size(relid)) as total_size,
                    pg_size_pretty(pg_relation_size(relid)) as table_size,
                    pg_size_pretty(pg_total_relation_size(relid) - 
                                 pg_relation_size(relid)) as index_size
                FROM pg_catalog.pg_statio_user_tables
                ORDER BY pg_total_relation_size(relid) DESC
            """
            table_stats = await self.db_service.fetch(query)
            
            # 获取索引使用情况
            query = """
                SELECT
                    schemaname,
                    relname as table_name,
                    indexrelname as index_name,
                    idx_scan as number_of_scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched
                FROM pg_catalog.pg_statio_user_indexes
                ORDER BY idx_scan DESC
            """
            index_stats = await self.db_service.fetch(query)
            
            return {
                "table_stats": table_stats,
                "index_stats": index_stats
            }
            
        except Exception as e:
            self.logger.error(f"分析表统计失败: {str(e)}")
            return {}
    
    async def suggest_indexes(self) -> List[str]:
        """建议创建的索引"""
        try:
            # 分析未使用的索引
            query = """
                SELECT
                    schemaname,
                    relname as table_name,
                    indexrelname as index_name,
                    idx_scan as number_of_scans
                FROM pg_catalog.pg_statio_user_indexes
                WHERE idx_scan = 0
                ORDER BY pg_relation_size(indexrelid) DESC
            """
            unused_indexes = await self.db_service.fetch(query)
            
            # 分析表扫描情况
            query = """
                SELECT
                    relname as table_name,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    idx_tup_fetch
                FROM pg_catalog.pg_stat_user_tables
                WHERE seq_scan > idx_scan
                ORDER BY seq_scan DESC
            """
            table_scans = await self.db_service.fetch(query)
            
            suggestions = []
            
            # 建议删除未使用的索引
            for index in unused_indexes:
                suggestions.append(
                    f"建议删除未使用的索引: {index['index_name']} "
                    f"在表 {index['table_name']} 上"
                )
            
            # 建议为经常全表扫描的表创建索引
            for table in table_scans:
                suggestions.append(
                    f"建议为表 {table['table_name']} 创建索引，"
                    f"当前全表扫描次数: {table['seq_scan']}"
                )
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"生成索引建议失败: {str(e)}")
            return []
    
    async def maintain_indexes(self):
        """维护索引"""
        try:
            # 重建碎片化的索引
            query = """
                SELECT schemaname, tablename, indexname 
                FROM pg_catalog.pg_indexes 
                WHERE schemaname = 'public'
            """
            indexes = await self.db_service.fetch(query)
            
            for index in indexes:
                # 重建索引
                await self.db_service.execute(
                    f"REINDEX INDEX {index['indexname']}"
                )
            
            self.logger.info("索引维护完成")
            
        except Exception as e:
            self.logger.error(f"维护索引失败: {str(e)}")
            raise 