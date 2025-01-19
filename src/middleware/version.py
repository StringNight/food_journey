"""版本中间件模块

处理API版本控制的中间件
"""

import re
import logging
from typing import Callable
from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from src.config.settings import settings

logger = logging.getLogger(__name__)

class VersionMiddleware(BaseHTTPMiddleware):
    """API版本控制中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求，添加版本信息
        
        Args:
            request: FastAPI请求对象
            call_next: 下一个处理函数
            
        Returns:
            Response: FastAPI响应对象
        """
        try:
            version = settings.APP_VERSION  # 默认使用配置文件中的版本

            # 从请求头获取版本
            if "X-API-Version" in request.headers:
                header_version = request.headers["X-API-Version"]
                if re.match(r"^\d+\.\d+$", header_version):
                    version = header_version
                else:
                    logger.warning(f"无效的API版本格式: {header_version}，使用默认版本")

            # 从URL路径获取版本
            path = request.url.path
            version_match = re.search(r"/api/v(\d+)", path)
            if version_match:
                url_version = f"{version_match.group(1)}.0"
                version = url_version

            response = await call_next(request)
            
            # 如果响应已经是 Response 类型，只添加版本头
            if isinstance(response, Response):
                response.headers["X-API-Version"] = version
                return response
                
            # 如果响应是字典，转换为 JSONResponse
            if isinstance(response, dict):
                return JSONResponse(
                    content=response,
                    status_code=200,
                    headers={"X-API-Version": version}
                )
                
            # 如果响应是其他类型，转换为字符串并包装在 JSONResponse 中
            return JSONResponse(
                content={"data": str(response)},
                status_code=200,
                headers={"X-API-Version": version}
            )
            
        except Exception as e:
            logger.error(f"版本中间件处理失败: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "服务器内部错误"},
                headers={"X-API-Version": settings.APP_VERSION}
            ) 