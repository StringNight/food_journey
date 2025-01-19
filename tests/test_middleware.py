"""中间件测试模块

测试各种中间件的功能
"""

import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from src.middleware.version import VersionMiddleware
from src.config.settings import settings

@pytest.mark.asyncio
async def test_version_middleware_default_version(test_client: AsyncClient):
    """测试版本中间件默认版本"""
    response = await test_client.get("/test")
    assert response.status_code == 200
    assert response.headers.get("X-API-Version") == settings.APP_VERSION

@pytest.mark.asyncio
async def test_version_middleware_custom_header(test_client: AsyncClient):
    """测试版本中间件自定义请求头"""
    response = await test_client.get(
        "/test",
        headers={"X-API-Version": "2.0"}
    )
    assert response.status_code == 200
    assert response.headers.get("X-API-Version") == "2.0"

@pytest.mark.asyncio
async def test_version_middleware_url_version(test_client: AsyncClient):
    """测试版本中间件URL版本"""
    response = await test_client.get("/api/v2/test")
    assert response.status_code == 200
    assert response.headers.get("X-API-Version") == "2.0"

@pytest.mark.asyncio
async def test_version_middleware_error_handling(test_client: AsyncClient):
    """测试版本中间件错误处理"""
    # 测试无效的版本号
    response = await test_client.get(
        "/test",
        headers={"X-API-Version": "invalid"}
    )
    assert response.status_code == 200
    assert response.headers.get("X-API-Version") == settings.APP_VERSION 