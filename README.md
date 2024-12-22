# 美食之旅 (Food Journey)

一个基于 FastAPI 和 Gradio 构建的智能菜谱推荐和管理系统。

## 功能特点

- 🤖 智能菜谱生成：基于用户食材和偏好自动生成菜谱
- 🎯 个性化推荐：根据用户口味和饮食习惯推荐菜品
- 👤 用户画像：记录和分析用户的烹饪偏好和技能水平
- 📊 营养分析：计算菜品的营养成分和健康指标
- 💬 实时交互：在烹饪过程中提供指导和建议
- ⭐ 收藏管理：支持收藏和管理喜爱的菜谱

## 技术栈

- 后端框架：FastAPI
- 前端界面：Gradio
- 数据库：SQLAlchemy + SQLite
- AI模型：LangChain + GPT
- 认证：JWT
- 缓存：Redis（可选）

## 系统要求

- Python 3.8+
- Redis（可选，用于缓存）
- 操作系统：支持 Windows/macOS/Linux

## 快速开始



2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 设置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，设置必要的环境变量
```

4. 运行项目
```bash
python main.py
```

5. 访问应用
- Web界面：http://localhost:7860
- API文档：http://localhost:8000/docs

## 项目结构

```
food_journey/
├── src/                    # 源代码目录
│   ├── auth/              # 认证相关模块
│   │   ├── jwt.py        # JWT认证实现
│   │   └── __init__.py
│   ├── config/            # 配置模块
│   │   ├── cors.py       # CORS配置
│   │   └── __init__.py
│   ├── middleware/        # 中间件
│   │   ├── rate_limiter.py    # 速率限制
│   │   ├── response_handler.py # 响应处理
│   │   └── __init__.py
│   ├── models/            # 数据模型
│   │   ├── user.py       # 用户模型
│   │   └── __init__.py
│   ├── routers/           # 路由处理
│   │   ├── auth.py       # 认证路由
│   │   ├── profile.py    # 用户画像路由
│   │   └── __init__.py
│   ├── schemas/           # 数据验证模式
│   │   ├── responses.py  # 响应模式
│   │   ├── user.py      # 用户相关模式
│   │   └── __init__.py
│   ├── async_handler.py   # 异步操作处理
│   ├── cache_manager.py   # 缓存管理
│   ├── database.py       # 数据库配置
│   ├── error_handler.py  # 错误处理
│   ├── llm_handler.py    # LLM模型处理
│   ├── recipe.py         # 菜谱模型
│   ├── recipe_manager.py # 菜谱管理
│   ├── user_profile.py   # 用户画像管理
│   ├── web_app.py        # Gradio Web界面
│   └── __init__.py
├── tests/                 # 测试目录
├── .env.example          # 环境变量示例
├── main.py               # 应用入口
├── README.md             # 项目文档
└── requirements.txt      # 项目依赖

```

## 核心模块说明

### 1. 菜谱管理 (src/recipe.py)

菜谱模型实现了以下功能：
- 菜谱的创建和验证
- 食材和步骤管理
- 营养成分计算
- 评分和评论系统
- 份量调整
- 成本估算

```python
from recipe import Recipe

# 创建菜谱
recipe = Recipe(
    title="红烧肉",
    ingredients=[...],
    steps=[...],
    author_id="user123"
)

# 调整份量
recipe.adjust_servings(4)

# 添加评分
recipe.add_rating(
    user_id="user456",
    rating=4.5,
    comment="非常美味！"
)
```

### 2. 用户认证 (src/auth/jwt.py)

提供了完整的JWT认证实现：
- 访问令牌和刷新令牌
- 令牌验证和刷新
- 用户认证中间件

```python
from auth.jwt import create_access_token

# 创建访问令牌
token = create_access_token({"sub": "user123"})
```

### 3. 缓存管理 (src/cache_manager.py)

支持多级缓存策略：
- Redis缓存（主要）
- 内存缓存（降级）
- 自动过期处理
- 批量操作支持

```python
from cache_manager import CacheManager

cache = CacheManager()
cache.set("key", "value", expire=3600)
value = cache.get("key")
```

### 4. LLM处理 (src/llm_handler.py)

AI模型集成：
- 菜谱生成
- 个性化推荐
- 烹饪指导
- 营养分析

```python
from llm_handler import LLMHandler

llm = LLMHandler()
recipe = await llm.generate_recipe(
    ingredients=["鸡胸肉", "西兰花"],
    preferences={"difficulty": "简单"}
)
```

### 5. Web界面 (src/web_app.py)

Gradio界面实现：
- 菜谱生成界面
- 推荐系统界面
- 用户画像管理
- 收藏夹管理

## API文档

完整的API文档可以在运行项目后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 配置说明

主要环境变量：
- `JWT_SECRET_KEY`: JWT密钥
- `DATABASE_URL`: 数据库连接URL
- `REDIS_URL`: Redis连接URL（可选）
- `OPENAI_API_KEY`: OpenAI API密钥

## 部署指南

1. 生产环境配置
```bash
# 设置生产环境变量
export ENV=production
export JWT_SECRET_KEY=your-secret-key
```

2. 使用Docker部署
```bash
docker build -t food-journey .
docker run -p 8000:8000 -p 7860:7860 food-journey
```

## 开发指南

1. 代码风格
- 遵循PEP 8规范
- 使用Black进行代码格式化
- 使用Flake8进行代码检查

2. 测试
```bash
# 运行测试
pytest tests/

# 带覆盖率报告
pytest --cov=src tests/
```

3. 新功能开发
- Fork项目
- 创建特性分支
- 提交PR

## 常见问题

1. Redis连接失败
- 检查Redis服务是否运行
- 验证连接URL是否正确
- 系统会自动降级到内存缓存

2. LLM生成失败
- 确认API密钥配置正确
- 检查网络连接
- 查看错误日志

## 更新日志

### v1.0.0 (2024-01)
- 初始版本发布
- 基础功能实现
- Web界面完成

### v1.1.0 (计划中)
- 添加更多AI模型支持
- 优化推荐算法
- 增加社交功能



# food_journey
