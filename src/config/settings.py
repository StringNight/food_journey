"""
应用程序设置模块

包含所有应用程序级别的配置参数
"""

import os
from typing import Dict, Any
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用程序设置类
    
    包含所有可配置的应用程序参数
    """
    
    # 基础设置
    APP_NAME: str = "Food Journey"
    APP_VERSION: str = "1.0"
    DEBUG: bool = False
    
    # 服务器设置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库设置
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./sql_app.db"
    )

    ssl_keyfile: str = os.getenv("SSL_KEYFILE", None)  # SSL私钥文件路径
    ssl_certfile: str = os.getenv("SSL_CERTFILE", None)  # SSL证书文件路径
    use_https: bool = os.getenv("USE_HTTPS", False) 
    
    # JWT设置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI设置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # 邮件设置
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # 文件上传设置
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png", "gif"}
    
    # 缓存设置
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    CACHE_TTL: int = 3600  # 1小时
    
    # 限流设置
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # 60秒
    
    # 账户锁定设置
    MAX_LOGIN_ATTEMPTS: int = 5  # 最大登录尝试次数
    LOCKOUT_DURATION: int = 15  # 锁定时长(分钟)
    
    class Config:
        env_file = ".env"
        extra = "allow"  # 允许额外的环境变量
        
    def get_all_settings(self) -> Dict[str, Any]:
        """获取所有设置
        
        Returns:
            Dict[str, Any]: 设置字典
        """
        return {
            key: getattr(self, key)
            for key in self.__fields__
            if not key.startswith("_")
        }

# 创建全局设置实例
settings = Settings()

# 导出设置实例
__all__ = ["settings"] 