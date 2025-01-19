# 导入必要的库
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取数据库URL，如果环境变量中没有设置，则使用SQLite作为默认数据库
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./sql_app.db"
)

# 如果是 PostgreSQL URL，转换为异步版本
if SQLALCHEMY_DATABASE_URL.startswith('postgresql://'):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        'postgresql://', 
        'postgresql+asyncpg://'
    )

# 创建异步数据库引擎
# 根据数据库URL选择合适的配置
if SQLALCHEMY_DATABASE_URL.startswith('sqlite'):
    # SQLite需要特殊的连接参数
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=False,
        future=True,
        pool_pre_ping=True
    )
else:
    # PostgreSQL和其他数据库使用标准配置
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=False,
        future=True,
        pool_pre_ping=True
    )

# 创建异步数据库会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# 创建基础模型类
Base = declarative_base()

# 数据库依赖项
async def get_db() -> AsyncSession:
    """获取数据库会话"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close() 