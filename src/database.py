from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# 获取数据库URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./food_journey.db")

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    # 对于SQLite，使用以下配置提高并发性能
    connect_args={
        "timeout": 30,  # 连接超时时间（秒）
        "check_same_thread": False,  # 允许跨线程使用连接
    },
    # 移除不支持的连接池参数
    # pool_size=5,  # 连接池大小
    # max_overflow=10,  # 最大溢出连接数
    # pool_timeout=30,  # 从连接池获取连接的超时时间
    pool_recycle=1800,  # 连接回收时间（秒）
    pool_pre_ping=True,  # 连接前ping一下，确保连接有效
)

# 创建会话工厂
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)

# 创建基类
Base = declarative_base()

# 创建获取数据库会话的函数
async def get_db():
    """获取数据库会话"""
    async with async_session() as session:
        try:
            yield session
            # 如果没有异常，提交事务
            await session.commit()
        except Exception:
            # 如果有异常，回滚事务
            await session.rollback()
            raise
        finally:
            # 确保关闭会话
            await session.close()