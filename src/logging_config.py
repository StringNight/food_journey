"""日志配置模块

此模块用于配置应用程序的日志设置，包括日志级别和格式。
"""

import logging

def configure_logging():
    """配置日志设置
    
    设置应用程序和第三方库的日志级别和格式。
    """
    # 设置第三方库的日志级别为 WARNING
    logging.getLogger('torio').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('passlib').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    
    # 配置根日志记录器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )