"""速率限制配置模块"""

import os
from slowapi import Limiter
from slowapi.util import get_remote_address

# 根据环境变量确定是否处于测试模式
is_test_mode = os.getenv("RATE_LIMIT_TEST_MODE", "false").lower() == "true"
test_max_requests = int(os.getenv("RATE_LIMIT_TEST_MAX_REQUESTS", "1000"))

# 根据测试模式设置不同的限制
default_limits = [f"{test_max_requests} per minute"] if is_test_mode else ["60 per minute"]

# 创建限速器实例
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=default_limits,
    headers_enabled=True
) 