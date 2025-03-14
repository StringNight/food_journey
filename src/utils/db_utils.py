import asyncio
import logging
from typing import Callable, Any, TypeVar, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')

async def execute_with_retry(
    db: AsyncSession,
    operation: Callable[[], Awaitable[T]],
    max_retries: int = 5,
    initial_delay: float = 0.5
) -> T:
    """安全执行数据库操作，带重试逻辑
    
    Args:
        db: 数据库会话
        operation: 要执行的操作函数
        max_retries: 最大重试次数
        initial_delay: 初始延迟时间（秒）
        
    Returns:
        操作结果
    """
    retry_count = 0
    retry_delay = initial_delay
    
    while True:
        try:
            # 执行操作
            result = await operation()
            # 尝试刷新会话
            await db.flush()
            return result
        except Exception as e:
            error_str = str(e).lower()
            if "database is locked" in error_str and retry_count < max_retries:
                retry_count += 1
                logging.warning(f"数据库锁定，等待重试 ({retry_count}/{max_retries})...")
                
                # 尝试回滚当前事务
                try:
                    await db.rollback()
                    logging.info("已回滚事务，准备重试")
                    # 开始新事务
                    await db.begin()
                except Exception as rollback_error:
                    logging.error(f"回滚事务失败: {rollback_error}")
                
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
            else:
                # 其他错误或已达到最大重试次数，则抛出
                raise