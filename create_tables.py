import asyncio
from src.database import engine, Base
import src.models  # 导入所有模型，确保模型注册到Base.metadata中

async def main():
    # 使用异步数据库连接创建所有表结构
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(main()) 