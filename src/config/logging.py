"""
日志配置模块

配置应用程序的日志系统，包括日志格式、输出位置等
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logging(
    level: str = "INFO",
    log_file: bool = True,
    console: bool = True,
    log_dir: str = "logs"
):
    """设置日志配置
    
    Args:
        level: 日志级别
        log_file: 是否输出到文件
        console: 是否输出到控制台
        log_dir: 日志文件目录
    """
    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 获取根日志记录器
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    if log_file:
        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建日志文件处理器
        log_file = os.path.join(
            log_dir,
            f"app-{datetime.now().strftime('%Y-%m-%d')}.log"
        )
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    if console:
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 记录初始化信息
    logger.info(
        "日志系统初始化完成 - 级别: %s, 文件: %s, 控制台: %s",
        level,
        log_file,
        console
    ) 