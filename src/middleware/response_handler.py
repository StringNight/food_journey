from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional
from datetime import datetime
import logging
from ..schemas.responses import StandardResponse

class ResponseHandler:
    """响应处理中间件
    
    统一处理API响应格式，添加通用字段，处理错误响应
    """
    
    def __init__(self):
        """初始化响应处理器"""
        self.logger = logging.getLogger(__name__)
    
    async def __call__(
        self,
        request: Request,
        call_next
    ) -> Any:
        """处理请求和响应
        
        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件或路由处理函数
            
        Returns:
            Response: 处理后的响应对象
        """
        response = None
        start_time = datetime.now()
        
        try:
            # 执行后续的中间件和路由处理
            response = await call_next(request)
            
            # 处理响应
            return await self._handle_response(
                request=request,
                response=response,
                start_time=start_time
            )
            
        except Exception as e:
            self.logger.error(f"请求处理失败: {e}")
            return await self._handle_error(
                request=request,
                error=e,
                start_time=start_time
            )
            
        finally:
            if response:
                await response.close()
    
    async def _handle_response(
        self,
        request: Request,
        response: Any,
        start_time: datetime
    ) -> JSONResponse:
        """处理成功响应
        
        Args:
            request: 请求对象
            response: 原始响应对象
            start_time: 请求开始时间
            
        Returns:
            JSONResponse: 处理后的响应
        """
        # 计算处理时间
        process_time = (datetime.now() - start_time).total_seconds()
        
        # 如果响应已经是JSONResponse，提取内容
        if isinstance(response, JSONResponse):
            data = response.body.decode()
            status_code = response.status_code
        else:
            data = response
            status_code = 200
        
        # 构建标准响应
        standard_response = StandardResponse(
            success=200 <= status_code < 300,
            message="操作成功" if 200 <= status_code < 300 else "操作失败",
            data=data,
            metadata={
                "path": str(request.url),
                "method": request.method,
                "process_time": process_time,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return JSONResponse(
            content=standard_response.dict(),
            status_code=status_code
        )
    
    async def _handle_error(
        self,
        request: Request,
        error: Exception,
        start_time: datetime
    ) -> JSONResponse:
        """处理错误响应
        
        Args:
            request: 请求对象
            error: 异常对象
            start_time: 请求开始时间
            
        Returns:
            JSONResponse: 错误响应
        """
        # 计算处理时间
        process_time = (datetime.now() - start_time).total_seconds()
        
        # 确定状态码和错误消息
        if hasattr(error, "status_code"):
            status_code = error.status_code
        else:
            status_code = 500
        
        error_message = str(error)
        if not error_message and status_code == 500:
            error_message = "服务器内部错误"
        
        # 构建错误响应
        error_response = StandardResponse(
            success=False,
            message=error_message,
            error_code=self._get_error_code(error),
            metadata={
                "path": str(request.url),
                "method": request.method,
                "process_time": process_time,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return JSONResponse(
            content=error_response.dict(),
            status_code=status_code
        )
    
    def _get_error_code(self, error: Exception) -> Optional[str]:
        """获取错误代码
        
        Args:
            error: 异常对象
            
        Returns:
            Optional[str]: 错误代码
        """
        if hasattr(error, "error_code"):
            return error.error_code
            
        # 根据异常类型返回通用错误代码
        error_type = type(error).__name__
        if error_type == "ValidationError":
            return "VALIDATION_ERROR"
        elif error_type == "HTTPException":
            return "HTTP_ERROR"
        elif error_type == "DatabaseError":
            return "DATABASE_ERROR"
        else:
            return "INTERNAL_ERROR"
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP
        
        Args:
            request: 请求对象
            
        Returns:
            str: 客户端IP地址
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0]
        return request.client.host
    
    def _get_request_metadata(self, request: Request) -> Dict:
        """获取请求元数据
        
        Args:
            request: 请求对象
            
        Returns:
            Dict: 请求相关的元数据
        """
        return {
            "path": str(request.url),
            "method": request.method,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("User-Agent"),
            "referer": request.headers.get("Referer"),
            "timestamp": datetime.now().isoformat()
        }