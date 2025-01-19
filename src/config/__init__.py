"""
配置模块

包含应用程序的所有配置项，包括数据库、缓存、日志等
"""

from .settings import Settings
from .cors import setup_cors
from .logging import setup_logging

config = Settings()

__all__ = [
    'config',
    'setup_cors',
    'setup_logging'
] 