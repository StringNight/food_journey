from sqlalchemy import create_engine
from src.database import Base
import src.models  # 导入所有模型，确保模型注册到 Base.metadata 中

# 使用同步引擎连接数据库
engine = create_engine("sqlite:///./sql_app.db", echo=True)

# 创建所有表结构
Base.metadata.create_all(engine)

print("数据库表结构已更新。") 