"""用户认证相关功能的测试模块"""

import pytest
from httpx import AsyncClient
import logging
from datetime import datetime, timedelta, UTC
import os
from jose import jwt
from src.config.settings import settings
import asyncio

# 设置日志
logger = logging.getLogger(__name__)

# 标记所有测试为异步
pytestmark = pytest.mark.asyncio

async def test_register_user(test_client: AsyncClient):
    """测试用户注册功能"""
    try:
        # 准备测试数据
        user_data = {
            "username": "newuser",
            "password": "Test123!@#"
        }
        
        # 发送注册请求
        logger.info("Attempting to register new user")
        response = await test_client.post(
            "/api/v1/auth/register",
            json=user_data
        )
        
        # 验证响应
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "user" in data
        assert data["user"]["username"] == user_data["username"]
        assert data["token_type"] == "bearer"
        assert data["user"]["is_active"] is True
        
        logger.info("User registration successful")
        
    except Exception as e:
        logger.error(f"Error in test_register_user: {e}")
        raise

async def test_login_user(test_client: AsyncClient):
    """测试用户登录功能"""
    try:
        # 准备测试数据
        user_data = {
            "username": "loginuser",
            "password": "Test123!@#"
        }
        
        # 先注册用户
        await test_client.post("/api/v1/auth/register", json=user_data)
        
        # 发送登录请求
        logger.info("Attempting to login")
        response = await test_client.post(
            "/api/v1/auth/login/json",
            json=user_data
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "access_token" in data["token"]
        assert "token_type" in data["token"]
        assert "expires_in" in data["token"]
        assert "user" in data
        assert data["user"]["username"] == user_data["username"]
        assert data["token"]["token_type"] == "bearer"
        
        logger.info("User login successful")
        
    except Exception as e:
        logger.error(f"Error in test_login_user: {e}")
        raise

async def test_get_profile(test_client: AsyncClient, test_user_token: str):
    """测试获取用户信息功能"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 获取个人信息
        logger.info("Attempting to get user profile")
        response = await test_client.get(
            "/api/v1/auth/profile",
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "created_at" in data
        assert "id" in data
        assert "is_active" in data
        
        logger.info("Profile retrieval successful")
        
    except Exception as e:
        logger.error(f"Error in test_get_profile: {e}")
        raise

async def test_duplicate_registration(test_client: AsyncClient):
    """测试重复注册"""
    try:
        # 准备测试数据
        user_data = {
            "username": "duplicateuser",
            "password": "Test123!@#"
        }
        
        # 第一次注册
        await test_client.post("/api/v1/auth/register", json=user_data)
        
        # 尝试重复注册
        logger.info("Attempting duplicate registration")
        response = await test_client.post(
            "/api/v1/auth/register",
            json=user_data
        )
        
        # 验证响应
        assert response.status_code == 400
        
        logger.info("Duplicate registration test successful")
        
    except Exception as e:
        logger.error(f"Error in test_duplicate_registration: {e}")
        raise

async def test_invalid_password_format(test_client: AsyncClient):
    """测试无效的密码格式"""
    try:
        # 测试太短的密码
        user_data = {
            "username": "invalidpassuser1",
            "password": "short"  # 密码太短
        }
        logger.info("Testing too short password")
        response = await test_client.post(
            "/api/v1/auth/register",
            json=user_data
        )
        assert response.status_code == 422
        
        # 测试没有大写字母的密码
        user_data["password"] = "test123!@#"
        logger.info("Testing password without uppercase letter")
        response = await test_client.post(
            "/api/v1/auth/register",
            json=user_data
        )
        assert response.status_code == 422
        
        # 测试没有小写字母的密码
        user_data["password"] = "TEST123!@#"
        logger.info("Testing password without lowercase letter")
        response = await test_client.post(
            "/api/v1/auth/register",
            json=user_data
        )
        assert response.status_code == 422
        
        # 测试没有数字的密码
        user_data["password"] = "TestTest!@#"
        logger.info("Testing password without number")
        response = await test_client.post(
            "/api/v1/auth/register",
            json=user_data
        )
        assert response.status_code == 422
        
        # 测试没有特殊字符的密码
        user_data["password"] = "TestTest123"
        logger.info("Testing password without special character")
        response = await test_client.post(
            "/api/v1/auth/register",
            json=user_data
        )
        assert response.status_code == 422
        
        logger.info("Invalid password format tests successful")
        
    except Exception as e:
        logger.error(f"Error in test_invalid_password_format: {e}")
        raise

async def test_avatar_upload(test_client: AsyncClient, test_user_token: str):
    """测试头像上传功能"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 创建一个最小的有效JPEG图片
        jpeg_header = bytes([
            0xFF, 0xD8,                    # SOI marker
            0xFF, 0xE0,                    # APP0 marker
            0x00, 0x10,                    # APP0 length (16 bytes)
            0x4A, 0x46, 0x49, 0x46, 0x00,  # "JFIF\0"
            0x01, 0x01,                    # version 1.1
            0x00,                          # units = none
            0x00, 0x01,                    # X density = 1
            0x00, 0x01,                    # Y density = 1
            0x00, 0x00                     # no thumbnail
        ])
        jpeg_footer = bytes([0xFF, 0xD9])  # EOI marker
        test_image = jpeg_header + b"test image data" + jpeg_footer
        
        files = {"file": ("test.jpg", test_image, "image/jpeg")}
        
        # 上传头像
        logger.info("Attempting to upload avatar")
        response = await test_client.post(
            "/api/v1/auth/avatar",
            files=files,
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "avatar_url" in data
        assert "username" in data
        assert "id" in data
        assert "is_active" in data
        
        logger.info("Avatar upload successful")
        
    except Exception as e:
        logger.error(f"Error in test_avatar_upload: {e}")
        raise

async def test_invalid_avatar_format(test_client: AsyncClient, test_user_token: str):
    """测试无效的头像格式"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 创建无效格式的文件
        test_file = b"fake text content"
        files = {"file": ("test.txt", test_file, "text/plain")}
        
        # 尝试上传
        logger.info("Attempting to upload invalid file format")
        response = await test_client.post(
            "/api/v1/auth/avatar",
            files=files,
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 400
        
        logger.info("Invalid avatar format test successful")
        
    except Exception as e:
        logger.error(f"Error in test_invalid_avatar_format: {e}")
        raise

async def test_refresh_token(test_client: AsyncClient, test_user_token: str):
    """测试刷新令牌功能"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 请求刷新令牌
        logger.info("Attempting to refresh token")
        response = await test_client.post(
            "/api/v1/auth/refresh",
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "access_token" in data["token"]
        assert "token_type" in data["token"]
        assert "expires_in" in data["token"]
        assert data["token"]["token_type"] == "bearer"
        
        # 验证新令牌有效
        decoded = jwt.decode(
            data["token"]["access_token"],
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert "sub" in decoded
        assert "refresh_time" in decoded
        
        logger.info("Token refresh successful")
        
    except Exception as e:
        logger.error(f"Error in test_refresh_token: {e}")
        raise

async def test_invalid_token(test_client: AsyncClient):
    """测试无效令牌"""
    try:
        headers = {"Authorization": "Bearer invalid_token"}
        
        # 尝试访问需要认证的端点
        logger.info("Attempting to access protected endpoint with invalid token")
        response = await test_client.get(
            "/api/v1/auth/profile",
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 401
        
        logger.info("Invalid token test successful")
        
    except Exception as e:
        logger.error(f"Error in test_invalid_token: {e}")
        raise

async def test_expired_token(test_client: AsyncClient):
    """测试过期令牌"""
    try:
        # 创建一个过期的令牌
        expired_time = datetime.now(UTC) - timedelta(minutes=60)
        expired_token = jwt.encode(
            {"exp": expired_time, "sub": "test_user"},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        # 尝试访问需要认证的端点
        logger.info("Attempting to access protected endpoint with expired token")
        response = await test_client.get(
            "/api/v1/auth/profile",
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 401
        
        logger.info("Expired token test successful")
        
    except Exception as e:
        logger.error(f"Error in test_expired_token: {e}")
        raise

async def test_missing_token(test_client: AsyncClient):
    """测试缺失令牌"""
    try:
        # 尝试访问需要认证的端点
        logger.info("Attempting to access protected endpoint without token")
        response = await test_client.get("/api/v1/auth/profile")
        
        # 验证响应
        assert response.status_code == 401
        
        logger.info("Missing token test successful")
        
    except Exception as e:
        logger.error(f"Error in test_missing_token: {e}")
        raise

async def test_account_lockout(test_client: AsyncClient):
    """测试账户锁定功能"""
    try:
        # 准备测试数据
        user_data = {
            "username": "lockoutuser",
            "password": "Test123!@#"
        }
        
        # 先注册用户
        await test_client.post("/api/v1/auth/register", json=user_data)
        
        # 尝试使用错误密码登录直到账户被锁定
        wrong_data = {
            "username": user_data["username"],
            "password": "WrongPass123!@#"
        }
        
        for i in range(settings.MAX_LOGIN_ATTEMPTS):
            response = await test_client.post(
                "/api/v1/auth/login/json",
                json=wrong_data
            )
            if i < settings.MAX_LOGIN_ATTEMPTS - 1:
                assert response.status_code == 401
            else:
                assert response.status_code == 403
                
        # 等待账户锁定时间结束
        logger.info("等待账户锁定时间结束")
        await asyncio.sleep(61)  # 等待61秒,确保锁定时间已过
        
        # 尝试使用正确的密码登录
        logger.info("尝试在锁定结束后登录")
        response = await test_client.post(
            "/api/v1/auth/login/json",
            json=user_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "access_token" in data["token"]
        
        logger.info("Account lockout test successful")
        
    except Exception as e:
        logger.error(f"Error in test_account_lockout: {e}")
        raise

async def test_large_avatar_upload(test_client: AsyncClient, test_user_token: str):
    """测试上传过大的头像文件"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 创建一个最小的有效JPEG图片，然后填充到超过5MB
        jpeg_header = bytes([
            0xFF, 0xD8,                    # SOI marker
            0xFF, 0xE0,                    # APP0 marker
            0x00, 0x10,                    # APP0 length (16 bytes)
            0x4A, 0x46, 0x49, 0x46, 0x00,  # "JFIF\0"
            0x01, 0x01,                    # version 1.1
            0x00,                          # units = none
            0x00, 0x01,                    # X density = 1
            0x00, 0x01,                    # Y density = 1
            0x00, 0x00                     # no thumbnail
        ])
        jpeg_footer = bytes([0xFF, 0xD9])  # EOI marker
        
        # 填充图像数据到超过5MB
        image_data = b"\xFF" * (5 * 1024 * 1024 + 1 - len(jpeg_header) - len(jpeg_footer))
        test_image = jpeg_header + image_data + jpeg_footer
        
        files = {"file": ("large.jpg", test_image, "image/jpeg")}
        
        # 尝试上传
        logger.info("Attempting to upload oversized avatar")
        response = await test_client.post(
            "/api/v1/auth/avatar",
            files=files,
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 413
        data = response.json()
        assert "detail" in data
        assert "文件大小超过限制" in data["detail"]
        
        logger.info("Large avatar upload test successful")
        
    except Exception as e:
        logger.error(f"Error in test_large_avatar_upload: {e}")
        raise

async def test_avatar_mime_type_validation(test_client: AsyncClient, test_user_token: str):
    """测试头像MIME类型验证"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 创建一个伪装的可执行文件
        logger.info("尝试上传伪装的可执行文件")
        test_file = b"fake executable"
        files = {"file": ("test.exe", test_file, "application/x-msdownload")}
        
        response = await test_client.post(
            "/api/v1/auth/avatar",
            files=files,
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "不支持的图片格式" in data["detail"]
        
        logger.info("Avatar MIME type validation test successful")
        
    except Exception as e:
        logger.error(f"Error in test_avatar_mime_type_validation: {e}")
        raise

async def test_rate_limit(test_client: AsyncClient):
    """测试API速率限制功能"""
    try:
        # 注册用户
        register_data = {
            "username": "test_rate_limit_user",
            "password": "Test123!@#"  # 符合密码要求的密码
        }
        response = await test_client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 201
        logger.info(f"用户注册成功: {response.json()}")
        
        # 使用注册的用户登录
        login_data = {
            "username": "test_rate_limit_user",
            "password": "Test123!@#"
        }
        response = await test_client.post("/api/v1/auth/login/json", json=login_data)
        assert response.status_code == 200
        token = response.json()["token"]["access_token"]
        logger.info(f"用户登录成功，获取到token")
        
        # 设置认证头
        headers = {"Authorization": f"Bearer {token}"}
        
        # 计数成功的请求
        successful_requests = 0
        
        # 发送多个请求测试速率限制
        for i in range(65):  # 发送65个请求，超过每分钟60个的限制
            response = await test_client.get("/api/v1/auth/profile", headers=headers)
            logger.info(f"请求 {i+1} 状态码: {response.status_code}")
            if response.status_code == 200:
                successful_requests += 1
            elif response.status_code == 429:
                logger.info(f"请求 {i+1} 触发速率限制，完整响应内容: {response.json()}")
                break
        
        # 确保至少有45个请求成功（考虑到注册和登录请求）
        assert successful_requests >= 45, f"只有 {successful_requests} 个请求成功，期望至少45个成功"
        
        # 发送一个额外的请求，应该被限制
        response = await test_client.get("/api/v1/auth/profile", headers=headers)
        response_data = response.json()
        logger.info(f"超出限制的请求的完整响应内容: {response_data}")
        assert response.status_code == 429, "超出限制的请求应该返回429状态码"
        assert "detail" in response_data, "响应中应该包含detail字段"
        
    except Exception as e:
        logger.error(f"Error in test_rate_limit: {e}")
        raise