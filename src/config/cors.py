from typing import List
from pydantic_settings import BaseSettings
from fastapi.middleware.cors import CORSMiddleware

class CORSSettings(BaseSettings):
    """CORS（跨源资源共享）配置类
    
    用于配置API的CORS策略，控制哪些来源可以访问API
    """
    
    # 允许的源列表
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",    # React开发服务器
        "http://localhost:8080",    # Vue开发服务器
        "http://localhost:5173",    # Vite开发服务器
    ]
    
    # 允许的HTTP方法
    ALLOWED_METHODS: List[str] = ["*"]  # 允许所有HTTP方法
    
    # 允许的HTTP头
    ALLOWED_HEADERS: List[str] = ["*"]  # 允许所有HTTP头
    
    # 是否允许携带凭证（如cookies）
    ALLOW_CREDENTIALS: bool = True
    
    # 预检请求的缓存时间（秒）
    MAX_AGE: int = 600  # 10分钟
    
    class Config:
        # 环境变量前缀
        # 例如：CORS_ALLOWED_ORIGINS 将映射到 ALLOWED_ORIGINS
        env_prefix = "CORS_"

def setup_cors(app):
    """设置 CORS 配置，允许 iOS 应用访问"""
    app.add_middleware(
        CORSMiddleware,
        # 允许的源，在开发时可以设置为 "*"，生产环境应该设置具体的域名
        allow_origins=["*"],
        # 允许的 HTTP 方法
        allow_methods=["*"],
        # 允许的 HTTP 头
        allow_headers=["*"],
        # 允许携带认证信息
        allow_credentials=True,
        # 允许的最大 age
        max_age=3600,
    )