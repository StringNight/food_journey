# 导入必要的库
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取数据库URL，如果环境变量中没有设置，则使用SQLite作为默认数据库
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./sql_app.db"
)

# 创建数据库引擎
# connect_args={"check_same_thread": False} 只在使用SQLite时需要
# 这个参数允许SQLite在多线程环境中工作
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# 创建数据库会话工厂
# autocommit=False：默认不自动提交事务
# autoflush=False：默认不自动刷新
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
# 所有的ORM模型都将继承这个基类
Base = declarative_base()

# 数据库依赖项
# 这个函数将在每个请求中创建一个新的数据库会话
# 使用完毕后自动关闭会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 