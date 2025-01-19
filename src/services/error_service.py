"""错误处理服务模块

提供统一的错误处理和日志记录功能
"""

import logging
import traceback
from typing import Dict, Any, Callable, TypeVar, ParamSpec
from functools import wraps
from datetime import datetime

# 类型变量
T = TypeVar('T')
P = ParamSpec('P')

class ErrorCode:
    """错误代码枚举"""
    UNKNOWN = "UNKNOWN"
    DATABASE = "DATABASE"
    VALIDATION = "VALIDATION"
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"

class AppError(Exception):
    """应用错误基类"""
    def __init__(
        self,
        code: str,
        message: str,
        details: Dict[str, Any] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

class ErrorService:
    """错误处理服务类"""
    
    def __init__(self):
        """初始化错误处理服务"""
        self.logger = logging.getLogger(__name__)
    
    def log_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None
    ) -> None:
        """记录错误信息
        
        Args:
            error: 异常对象
            context: 错误上下文信息
        """
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        
        if isinstance(error, AppError):
            error_info.update({
                "code": error.code,
                "details": error.details
            })
        
        self.logger.error(
            "发生错误: %(type)s - %(message)s",
            error_info
        )
        self.logger.debug("错误详情: %s", error_info)

def error_handler(func: Callable[P, T]) -> Callable[P, T]:
    """错误处理装饰器
    
    用于包装异步函数，提供统一的错误处理
    
    Args:
        func: 要包装的异步函数
        
    Returns:
        包装后的函数
    """
    error_service = ErrorService()
    
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return await func(*args, **kwargs)
            
        except AppError as e:
            # 记录应用错误
            error_service.log_error(e, {
                "function": func.__name__,
                "args": args,
                "kwargs": kwargs
            })
            raise
            
        except Exception as e:
            # 记录未知错误
            error_service.log_error(e, {
                "function": func.__name__,
                "args": args,
                "kwargs": kwargs
            })
            # 转换为应用错误
            raise AppError(
                code=ErrorCode.UNKNOWN,
                message="发生未知错误",
                details={"original_error": str(e)}
            )
    
    return wrapper 