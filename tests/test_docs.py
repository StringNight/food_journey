"""API文档测试模块

测试API文档的可访问性和内容
"""

import pytest
from httpx import AsyncClient
import json

@pytest.mark.asyncio
async def test_openapi_schema(test_client: AsyncClient):
    """测试OpenAPI模式的可访问性和内容"""
    response = await test_client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    # 验证基本信息
    assert schema["info"]["title"] == "美食之旅 API"
    assert "美食之旅后端API文档" in schema["info"]["description"]
    assert schema["info"]["version"] == "1.0.0"
    
    # 验证API路径
    paths = schema["paths"]
    assert any(path.startswith("/api/v1/auth/register") for path in paths)
    assert any(path.startswith("/api/v1/auth/login") for path in paths)
    assert any(path.startswith("/api/v1/profile") for path in paths)

@pytest.mark.asyncio
async def test_swagger_ui(test_client: AsyncClient):
    """测试Swagger UI的可访问性"""
    response = await test_client.get("/api/v1/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()

@pytest.mark.asyncio
async def test_redoc_ui(test_client: AsyncClient):
    """测试ReDoc UI的可访问性"""
    response = await test_client.get("/api/v1/redoc")
    assert response.status_code == 200
    assert "redoc" in response.text.lower()

@pytest.mark.asyncio
async def test_chinese_descriptions(test_client: AsyncClient):
    """测试API文档中的中文描述"""
    response = await test_client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    
    # 验证标题和描述是否包含中文
    assert "美食之旅" in schema["info"]["title"]
    assert "美食之旅后端API文档" in schema["info"]["description"]
    
    # 验证标签描述是否包含中文
    has_chinese_tag = False
    for tag in schema["tags"]:
        if any('\u4e00' <= char <= '\u9fff' for char in tag["description"]):
            has_chinese_tag = True
            break
    assert has_chinese_tag, "标签描述中应该包含中文" 