"""配置管理模块

提供统一的配置管理功能，支持不同环境的配置
"""

import os
from pathlib import Path
from typing import Dict, Any
from pydantic import BaseSettings, Field

class DatabaseConfig(BaseSettings):
    """数据库配置"""
    host: str = Field("localhost", env="DB_HOST")
    port: int = Field(5432, env="DB_PORT")
    database: str = Field("food_journey", env="DB_NAME")
    user: str = Field("postgres", env="DB_USER")
    password: str = Field("postgres", env="DB_PASSWORD")
    min_connections: int = Field(5, env="DB_MIN_CONN")
    max_connections: int = Field(20, env="DB_MAX_CONN")
    
    @property
    def dsn(self) -> str:
        """获取数据库连接字符串"""
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )
    
    class Config:
        env_file = ".env"

class JWTConfig(BaseSettings):
    """JWT配置"""
    secret_key: str = Field("test_secret_key_for_testing_only", env="JWT_SECRET_KEY")
    algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        30,
        env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    class Config:
        env_file = ".env"

class AppConfig(BaseSettings):
    """应用配置"""
    env: str = Field("development", env="APP_ENV")
    debug: bool = Field(False, env="APP_DEBUG")
    host: str = Field("127.0.0.1", env="APP_HOST")
    port: int = Field(8000, env="APP_PORT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # 头像上传配置
    MAX_AVATAR_SIZE: int = Field(5 * 1024 * 1024, env="MAX_AVATAR_SIZE")  # 默认5MB
    ALLOWED_AVATAR_TYPES: list = Field(
        ["image/jpeg", "image/png", "image/gif"],
        env="ALLOWED_AVATAR_TYPES"
    )
    
    # 文件存储配置
    UPLOAD_DIR: str = Field("uploads", env="UPLOAD_DIR")  # 上传文件根目录
    AVATAR_DIR: str = Field("avatars", env="AVATAR_DIR")  # 头像存储子目录
    AVATAR_URL_PREFIX: str = Field("/static/avatars", env="AVATAR_URL_PREFIX")  # 头像URL前缀
    
    # 子配置
    db: DatabaseConfig = DatabaseConfig()
    jwt: JWTConfig = JWTConfig()
    
    # 项目路径
    @property
    def root_dir(self) -> Path:
        """获取项目根目录"""
        return Path(__file__).parent.parent
    
    @property
    def log_dir(self) -> Path:
        """获取日志目录"""
        return self.root_dir / "logs"
    
    @property
    def static_dir(self) -> Path:
        """获取静态文件目录"""
        return self.root_dir / "static"
    
    def get_cors_origins(self) -> list:
        """获取CORS允许的源"""
        origins = os.getenv("CORS_ORIGINS", "")
        if not origins:
            return ["*"] if self.debug else []
        return origins.split(",")
    
    class Config:
        env_file = ".env"

# 创建配置实例
config = AppConfig()

# 环境特定的配置
env_configs: Dict[str, Dict[str, Any]] = {
    "development": {
        "debug": True,
        "log_level": "DEBUG",
    },
    "testing": {
        "debug": True,
        "log_level": "DEBUG",
        "db": {
            "database": "food_journey_test"
        }
    },
    "production": {
        "debug": False,
        "log_level": "WARNING",
    }
}

# 应用环境特定的配置
if config.env in env_configs:
    for key, value in env_configs[config.env].items():
        if isinstance(value, dict):
            # 更新嵌套配置
            current = getattr(config, key)
            for k, v in value.items():
                setattr(current, k, v)
        else:
            # 更新顶级配置
            setattr(config, key, value) 