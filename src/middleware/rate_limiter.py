from fastapi import Request, HTTPException, status
from typing import Dict, Tuple
import time
import logging
from datetime import datetime, timedelta

class RateLimiter:
    """速率限制中间件
    
    实现基于时间窗口的API访问速率限制
    支持按IP和用户ID进行限制
    """
    
    def __init__(self):
        """初始化速率限制器
        
        创建请求计数器和配置默认限制
        """
        # 请求计数器 {key: (count, start_time)}
        self.requests: Dict[str, Tuple[int, float]] = {}
        
        # 默认限制配置
        self.window_size = 60  # 时间窗口大小（秒）
        self.max_requests = 100  # 每个窗口允许的最大请求数
        self.whitelist_ips = {'127.0.0.1'}  # IP白名单
    
    def _get_key(self, request: Request) -> str:
        """生成请求的唯一键
        
        基于IP地址和可选的用户ID生成唯一标识
        
        Args:
            request: FastAPI请求对象
            
        Returns:
            str: 请求的唯一键
        """
        # 获取客户端IP
        ip = request.client.host
        
        # 尝试获取用户ID（如果已认证）
        user_id = getattr(request.state, 'user_id', None)
        
        # 如果有用户ID，将IP和用户ID组合作为键
        if user_id:
            return f"{ip}:{user_id}"
        return ip
    
    def _is_rate_limited(self, key: str) -> bool:
        """检查是否超出速率限制
        
        Args:
            key: 请求的唯一键
            
        Returns:
            bool: 是否超出限制
        """
        current_time = time.time()
        
        # 获取当前计数和开始时间
        count, start_time = self.requests.get(key, (0, current_time))
        
        # 如果已经超过时间窗口，重置计数
        if current_time - start_time >= self.window_size:
            count = 0
            start_time = current_time
        
        # 更新计数
        count += 1
        self.requests[key] = (count, start_time)
        
        # 检查是否超出限制
        return count > self.max_requests
    
    def _clean_old_records(self):
        """清理过期的记录
        
        删除超过时间窗口的请求记录
        """
        current_time = time.time()
        expired_keys = [
            key for key, (_, start_time) in self.requests.items()
            if current_time - start_time >= self.window_size
        ]
        for key in expired_keys:
            del self.requests[key]
    
    async def __call__(self, request: Request, call_next):
        """处理请求的中间件方法
        
        Args:
            request: FastAPI请求对象
            call_next: 下一个处理函数
            
        Returns:
            Response: 响应对象
            
        Raises:
            HTTPException: 当超出速率限制时抛出
        """
        # 定期清理过期记录
        self._clean_old_records()
        
        # 获取请求键
        key = self._get_key(request)
        
        # 检查是否在白名单中
        if request.client.host in self.whitelist_ips:
            return await call_next(request)
        
        # 检查是否超出限制
        if self._is_rate_limited(key):
            logging.warning(f"请求超出速率限制: {key}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁，请稍后再试"
            )
        
        # 继续处理请求
        return await call_next(request)
    
    def update_limits(self, window_size: int = None, max_requests: int = None):
        """更新速率限制配置
        
        Args:
            window_size: 新的时间窗口大小（秒）
            max_requests: 新的最大请求数
        """
        if window_size is not None:
            self.window_size = window_size
        if max_requests is not None:
            self.max_requests = max_requests
    
    def add_to_whitelist(self, ip: str):
        """添加IP到白名单
        
        Args:
            ip: 要添加的IP地址
        """
        self.whitelist_ips.add(ip)
    
    def remove_from_whitelist(self, ip: str):
        """从白名单移除IP
        
        Args:
            ip: 要移除的IP地址
        """
        self.whitelist_ips.discard(ip)