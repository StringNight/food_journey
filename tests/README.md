# 美食之旅测试指南

本文档提供了关于如何运行、维护和扩展测试用例的指导。

## 测试环境设置

### 安装依赖

首先，确保已安装所有测试依赖：

```bash
pip install -r requirements.txt
pytest pytest-asyncio pytest-xdist httpx aiosqlite matplotlib
```

### 环境变量配置

测试使用内存数据库和模拟的第三方服务。如果需要，可以通过环境变量进行配置：

```bash
# 设置测试环境
export APP_ENV=testing
export TESTING=true
export DATABASE_URL=sqlite+aiosqlite:///:memory:
```

## 运行测试

### 运行所有测试

```bash
pytest
```

### 运行特定测试文件

```bash
# 运行认证测试
pytest tests/test_auth.py

# 运行食谱相关测试
pytest tests/test_recipes.py

# 运行集成测试
pytest tests/test_comprehensive.py
pytest tests/test_frontend_integration.py

# 运行性能测试
pytest tests/test_performance.py
```

### 运行特定测试用例

```bash
# 运行特定测试函数
pytest tests/test_auth.py::test_register_user

# 运行特定测试类中的特定测试方法
pytest tests/test_frontend_integration.py::TestRecipeIntegration::test_recipe_listing_and_details
```

### 并行运行测试

```bash
pytest -xvs -n auto
```

## 测试文件说明

### 基础测试文件

- **test_auth.py**: 测试用户认证相关功能
- **test_recipes.py**: 测试食谱管理功能 
- **test_favorites.py**: 测试收藏功能
- **test_chat.py**: 测试聊天功能
- **test_workout.py**: 测试运动记录功能
- **test_docs.py**: 测试API文档生成
- **test_middleware.py**: 测试中间件功能

### 集成测试文件

- **test_comprehensive.py**: 端到端综合测试，测试用户完整操作流程
- **test_frontend_integration.py**: 前后端集成测试，模拟前端调用后端API

### 性能测试文件

- **test_performance.py**: 性能测试，检测高负载下系统表现

### 测试配置文件

- **conftest.py**: 测试配置，包含各种测试夹具和辅助函数

## 测试工具

### 测试夹具

- **test_client**: AsyncClient的实例，用于发送异步HTTP请求
- **test_app**: FastAPI应用实例
- **test_user_token**: 测试用户的认证令牌
- **mock_ai_service**: 模拟AI服务的响应

### 辅助函数

测试模块中包含多个辅助函数，用于简化测试过程：

- 用户注册和登录
- 创建和获取食谱
- 更新用户档案
- 记录和获取锻炼
- 并发请求模拟

## 添加新测试

### 测试文件结构

```python
"""测试模块说明"""

import pytest
import logging
from httpx import AsyncClient

# 设置日志
logger = logging.getLogger(__name__)

# 标记所有测试为异步
pytestmark = pytest.mark.asyncio

async def test_feature(test_client: AsyncClient, test_user_token: str):
    """测试特定功能"""
    # 测试逻辑
    pass
```

### 测试类结构

```python
class TestFeature:
    """测试特定功能集合"""
    
    async def test_specific_function(self, test_client: AsyncClient, test_user_token: str):
        """测试特定功能点"""
        # 测试逻辑
        pass
```

## 性能测试结果解读

性能测试会生成响应时间分布图表和JSON格式的统计数据，存储在`performance_reports`目录中。

统计数据包括：
- 最小响应时间
- 最大响应时间
- 平均响应时间
- 中位响应时间
- 95%分位响应时间
- 标准差

## 常见问题排查

### 测试失败

1. 检查错误日志，了解失败原因
2. 确认测试环境变量设置正确
3. 检查模拟服务配置

### 超时问题

1. 调整测试超时设置：`pytest --timeout=300`
2. 减少并发测试数量

### 数据库问题

1. 确保使用内存数据库进行测试
2. 检查测试后是否正确清理数据

## 注意事项

1. 测试用例应该相互独立，不依赖其他测试的执行结果
2. 使用模拟服务替代真实的第三方API调用
3. 保持测试覆盖率，确保关键功能都有测试
4. 定期运行性能测试，监控系统性能变化 