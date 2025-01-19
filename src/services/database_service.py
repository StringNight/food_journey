"""数据库服务模块

提供数据库连接和操作功能
"""

import asyncpg
import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from ..config import config

class DatabaseService:
    """数据库服务类
    
    管理数据库连接池和提供数据库操作方法
    """
    
    def __init__(self):
        """初始化数据库服务"""
        self.pool = None
        self.logger = logging.getLogger(__name__)
        
    async def init_pool(self, dsn: Optional[str] = None):
        """初始化连接池
        
        Args:
            dsn: 数据库连接字符串，默认使用配置中的DSN
        """
        try:
            # 使用配置或传入的DSN
            self.pool = await asyncpg.create_pool(
                dsn or config.db.dsn,
                min_size=config.db.min_connections,
                max_size=config.db.max_connections,
                command_timeout=60
            )
            self.logger.info(
                "数据库连接池初始化成功 - host: %s, database: %s",
                config.db.host,
                config.db.database
            )
            
        except Exception as e:
            self.logger.error(f"初始化数据库连接池失败: {str(e)}")
            raise
    
    @asynccontextmanager
    async def connection(self):
        """获取数据库连接的上下文管理器
        
        用法:
            async with db_service.connection() as conn:
                await conn.execute(...)
        """
        if not self.pool:
            raise RuntimeError("数据库连接池未初始化")
            
        try:
            async with self.pool.acquire() as conn:
                yield conn
        except Exception as e:
            self.logger.error(f"数据库操作失败: {str(e)}")
            raise
    
    async def execute(self, query: str, *args) -> str:
        """执行数据库写操作
        
        Args:
            query: SQL查询语句
            *args: 查询参数
            
        Returns:
            str: 操作结果
        """
        async with self.connection() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """执行数据库读操作并返回多行结果
        
        Args:
            query: SQL查询语句
            *args: 查询参数
            
        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """
        async with self.connection() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """执行数据库读操作并返回单行结果
        
        Args:
            query: SQL查询语句
            *args: 查询参数
            
        Returns:
            Optional[Dict[str, Any]]: 查询结果，如果没有找到则返回None
        """
        async with self.connection() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def fetch_val(self, query: str, *args) -> Any:
        """执行数据库读操作并返回单个值
        
        Args:
            query: SQL查询语句
            *args: 查询参数
            
        Returns:
            Any: 查询结果值
        """
        async with self.connection() as conn:
            return await conn.fetchval(query, *args)
    
    async def transaction(self):
        """获取事务上下文管理器
        
        用法:
            async with db_service.transaction() as conn:
                await conn.execute(...)
                await conn.execute(...)
        """
        if not self.pool:
            raise RuntimeError("数据库连接池未初始化")
            
        try:
            conn = await self.pool.acquire()
            tr = conn.transaction()
            await tr.start()
            
            try:
                yield conn
                await tr.commit()
            except Exception:
                await tr.rollback()
                raise
            finally:
                await self.pool.release(conn)
                
        except Exception as e:
            self.logger.error(f"事务操作失败: {str(e)}")
            raise
    
    async def close(self):
        """关闭数据库连接池"""
        if self.pool:
            await self.pool.close()
            self.logger.info("数据库连接池已关闭") 