"""测试配置模块

提供测试环境配置和通用的测试夹具
"""

import os
import sys
import asyncio
import pytest
import pytest_asyncio
import logging
import shutil
from typing import AsyncGenerator, Generator
from fastapi import FastAPI, APIRouter
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import warnings
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

# 忽略警告
warnings.filterwarnings("ignore", category=DeprecationWarning)

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 设置测试环境
os.environ["APP_ENV"] = "testing"
os.environ["TESTING"] = "true"
os.environ["SECRET_KEY"] = "test_secret_key"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["RATE_LIMIT_TEST_MODE"] = "true"  # 添加速率限制测试模式
os.environ["RATE_LIMIT_TEST_MAX_REQUESTS"] = "1000"  # 设置测试环境的请求限制
os.environ["LOCKOUT_DURATION"] = "1"  # 设置测试环境的账户锁定时间为1秒
os.environ["MAX_LOGIN_ATTEMPTS"] = "5"  # 设置最大登录尝试次数

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 使用异步SQLite作为测试数据库
engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# 创建异步会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# 设置 pytest-asyncio 的配置
pytest.ini_options = {
    "asyncio_mode": "strict",
    "asyncio_default_fixture_loop_scope": "function"
}

# 设置测试上传目录
TEST_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "test_uploads")
os.environ["UPLOAD_DIR"] = TEST_UPLOAD_DIR

async def init_db():
    """初始化数据库"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        logger.info("测试数据库初始化成功")
    except Exception as e:
        logger.error(f"测试数据库初始化失败: {e}")
        raise

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """设置数据库，每个测试前重置"""
    await init_db()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("测试数据库清理完成")

# 导入应用实例（确保在设置环境变量后导入）
from src.database import Base, get_db
from src.config.settings import settings
from src.main import app

# 创建测试路由
test_router = APIRouter()

@test_router.get("/test")
async def test_endpoint():
    return {"message": "test"}

@test_router.get("/api/v2/test")
async def test_endpoint_v2():
    return {"message": "test v2"}

@pytest_asyncio.fixture
async def test_app() -> FastAPI:
    """创建测试应用实例"""
    # 注册测试路由
    app.include_router(test_router)
    app.dependency_overrides[get_db] = get_test_db
    
    # 设置速率限制器为每分钟60个请求
    from src.main import limiter
    limiter.is_testing = True
    limiter.test_max_requests = 1000  # 增加到每分钟1000个请求
    limiter.test_window_size = 60   # 60秒时间窗口
    
    yield app
    app.dependency_overrides.clear()

async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
    """获取测试数据库会话"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
            logger.info("测试数据库会话已关闭")

@pytest_asyncio.fixture
async def test_client(test_app: FastAPI) -> AsyncClient:
    """创建测试客户端"""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        timeout=10.0
    ) as client:
        yield client

@pytest_asyncio.fixture
async def test_user_token(test_client: AsyncClient) -> str:
    """创建测试用户并返回其token"""
    try:
        # 注册用户数据
        user_data = {
            "username": "testuser",
            "password": "Test@123456"  # 符合密码验证规则的测试密码
        }
        
        # 注册用户
        logger.info("开始注册测试用户")
        response = await test_client.post(
            "/api/v1/auth/register",
            json=user_data
        )
        assert response.status_code == 201, f"用户注册失败: {response.text}"
        
        # 登录获取token
        logger.info("开始登录测试用户")
        response = await test_client.post(
            "/api/v1/auth/login/json",
            json={
                "username": user_data["username"],
                "password": user_data["password"]
            }
        )
        assert response.status_code == 200, f"用户登录失败: {response.text}"
        data = response.json()
        token = data["token"]["access_token"]
        logger.info("成功获取测试用户token")
        return token
    except Exception as e:
        logger.error(f"测试用户token获取失败: {e}")
        raise

@pytest.fixture
def test_recipe_data():
    """创建测试菜谱数据"""
    return {
        "title": "测试菜谱",
        "description": "这是一个测试菜谱的描述",
        "ingredients": [
            {"name": "食材1", "amount": "100克"},
            {"name": "食材2", "amount": "200毫升"}
        ],
        "steps": [
            {"step": "1", "description": "第一步的描述"},
            {"step": "2", "description": "第二步的描述"}
        ],
        "cooking_time": 30,
        "difficulty": "简单",
        "cuisine_type": "中餐"
    }

@pytest_asyncio.fixture(autouse=True)
async def setup_test_environment():
    """设置测试环境"""
    # 创建测试上传目录
    os.makedirs(os.path.join(TEST_UPLOAD_DIR, "avatars"), exist_ok=True)
    os.makedirs(os.path.join(TEST_UPLOAD_DIR, "voices"), exist_ok=True)
    os.makedirs(os.path.join(TEST_UPLOAD_DIR, "images"), exist_ok=True)
    
    yield
    
    # 清理测试上传目录
    if os.path.exists(TEST_UPLOAD_DIR):
        shutil.rmtree(TEST_UPLOAD_DIR)

@pytest.fixture
def mock_ai_service():
    """模拟AI服务的响应"""
    with patch("src.routers.chat.ai_client") as mock_client:
        # 模拟文本聊天响应
        mock_client.chat = AsyncMock(return_value={
            "content": "这是一个测试回复",
            "suggestions": ["建议1", "建议2"]
        })
        
        # 模拟语音转文本响应
        mock_client.process_voice = AsyncMock(return_value="这是语音转文本的结果")
        
        # 模拟食物识别响应
        mock_client.recognize_food = AsyncMock(return_value={
            "success": True,
            "image_url": "/images/test/food.jpg",
            "food_items": [{
                "name": "苹果",
                "confidence": 95,
                "calorie": 52
            }]
        })
        
        yield mock_client 