"""
错误处理中间件

提供全局错误处理和异常管理功能
"""

from typing import Optional, Dict, Any, Callable
import logging
from functools import wraps
from tenacity import retry, stop_after_attempt, wait_exponential
import traceback
from datetime import datetime

class CustomException(Exception):
    """自定义异常基类
    
    所有自定义异常的基类，包含错误消息和错误代码
    """
    def __init__(self, message: str, error_code: str):
        """初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误代码
        """
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class DatabaseError(CustomException):
    """数据库错误
    
    表示数据库操作相关的错误
    """
    pass

class NetworkError(CustomException):
    """网络错误
    
    表示网络通信相关的错误
    """
    pass

class ValidationError(CustomException):
    """验证错误
    
    表示数据验证相关的错误
    """
    pass

def error_handler(func: Callable) -> Callable:
    """错误处理装饰器
    
    用于包装异步函数，统一处理各种类型的异常
    
    Args:
        func: 要装饰的异步函数
        
    Returns:
        Callable: 装饰后的函数
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DatabaseError as e:
            logging.error(f"数据库错误: {e.message}")
            # 可以在这里添加数据库重连逻辑
            raise
        except NetworkError as e:
            logging.error(f"网络错误: {e.message}")
            # 可以在这里添加重试逻辑
            raise
        except ValidationError as e:
            logging.error(f"验证错误: {e.message}")
            # 直接返回错误信息给用户
            return {"error": e.message, "code": e.error_code}
        except Exception as e:
            # 记录未预期的错误
            logging.error(f"未预期的错误: {str(e)}")
            logging.error(traceback.format_exc())
            # 返回通用错误信息
            return {"error": "服务器内部错误", "code": "INTERNAL_ERROR"}
    return wrapper

class ErrorHandler:
    """错误处理器类
    
    提供错误日志记录和错误恢复机制
    """
    
    def __init__(self):
        """初始化错误处理器
        
        创建错误日志列表
        """
        self.error_log = []
    
    def log_error(self, error: Exception, context: Dict[str, Any]):
        """记录错误信息
        
        Args:
            error: 异常对象
            context: 错误发生时的上下文信息
        """
        error_info = {
            "timestamp": datetime.now(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "traceback": traceback.format_exc()
        }
        self.error_log.append(error_info)
        logging.error(f"错误信息: {error_info}")
    
    @retry(stop=stop_after_attempt(3),
           wait=wait_exponential(multiplier=1, min=4, max=10))
    async def retry_operation(self, func: Callable, *args, **kwargs):
        """重试操作
        
        使用指数退避策略重试失败的操作
        
        Args:
            func: 要重试的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 函数执行结果
            
        Raises:
            Exception: 当重试全部失败时抛出
        """
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            self.log_error(e, {
                "function": func.__name__,
                "args": args,
                "kwargs": kwargs
            })
            raise
    
    def handle_database_error(self, error: DatabaseError):
        """处理数据库错误
        
        Args:
            error: 数据库错误对象
        """
        # 实现数据库错误恢复逻辑
        pass
    
    def handle_network_error(self, error: NetworkError):
        """处理网络错误
        
        Args:
            error: 网络错误对象
        """
        # 实现网络错误恢复逻辑
        pass
    
    def handle_validation_error(self, error: ValidationError):
        """处理验证错误
        
        Args:
            error: 验证错误对象
        """
        # 实现验证错误处理逻辑
        pass

# 创建全局错误处理器实例
error_handler_instance = ErrorHandler()

# 导出错误处理器实例和装饰器
__all__ = ["error_handler_instance", "error_handler"] 