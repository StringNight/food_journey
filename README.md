# Food Journey Backend

Food Journey是一个智能饮食和健康管理系统的后端服务。本项目使用FastAPI框架构建，提供了完整的用户管理、食谱管理、健康数据追踪和AI辅助功能。

## 技术栈

- Python 3.8+
- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT认证
- OpenAI API集成

## 项目结构

```
food_journey_backend/
├── src/                    # 源代码目录
│   ├── routers/           # API路由处理器
│   │   ├── __init__.py   # 路由包初始化
│   │   ├── api.py        # 主路由聚合器
│   │   ├── auth.py       # 认证相关路由
│   │   ├── chat.py       # 聊天功能路由
│   │   ├── favorites.py  # 收藏管理路由
│   │   ├── profile.py    # 用户档案路由
│   │   ├── recipes.py    # 食谱管理路由
│   │   └── workout.py    # 运动记录路由
│   ├── models/           # 数据库模型
│   │   ├── __init__.py   # 模型包初始化
│   │   ├── user.py       # 用户模型
│   │   ├── recipe.py     # 食谱模型
│   │   ├── favorite.py   # 收藏模型
│   │   ├── chat.py       # 聊天消息模型
│   │   ├── nutrition.py  # 营养记录模型
│   │   ├── profile.py    # 用户档案模型
│   │   └── workout.py    # 运动记录模型
│   ├── schemas/          # Pydantic模型/数据验证
│   │   ├── __init__.py   # 模式包初始化
│   │   ├── auth.py       # 认证相关模型
│   │   ├── chat.py       # 聊天相关模型
│   │   ├── favorite.py   # 收藏相关模型
│   │   ├── recipe.py     # 食谱相关模型
│   │   ├── profile.py    # 用户档案模型
│   │   ├── responses.py  # 通用响应模型
│   │   ├── user.py       # 用户相关模型
│   │   └── workout.py    # 运动相关模型
│   ├── services/         # 业务逻辑服务
│   │   ├── __init__.py   # 服务包初始化
│   │   ├── ai_service_client.py    # AI服务客户端
│   │   ├── recipe_service.py       # 食谱服务
│   │   ├── user_service.py         # 用户服务
│   │   └── recommendation_service.py # 推荐服务
│   ├── auth/            # 认证相关功能
│   │   ├── __init__.py  # 认证包初始化
│   │   └── jwt.py       # JWT处理
│   ├── middleware/      # 中间件
│   │   ├── __init__.py  # 中间件包初始化
│   │   ├── rate_limiter.py    # 请求限流
│   │   ├── error_handler.py   # 错误处理
│   │   ├── version.py         # API版本控制
│   │   └── response_handler.py # 响应处理
│   ├── config/          # 配置文件
│   │   ├── __init__.py  # 配置包初始化
│   │   ├── settings.py  # 应用配置
│   │   └── cors.py      # CORS配置
│   ├── docs/           # 文档目录
│   ├── __init__.py     # 主包初始化
│   ├── main.py         # 应用入口点
│   ├── app.py          # FastAPI应用配置
│   ├── database.py     # 数据库配置
│   ├── input_processor.py # 输入处理器
│   ├── validators.py    # 数据验证器
│   ├── async_handler.py # 异步操作处理器
│   ├── cache_manager.py # 缓存管理器
│   ├── web_app.py      # Web应用界面
│   └── logging_config.py # 日志配置
├── ai_service/          # AI服务集成
│   ├── src/            # AI服务源代码
│   │   ├── config/     # AI服务配置
│   │   ├── routers/    # AI服务路由
│   │   │   ├── image.py    # 图像处理路由
│   │   │   ├── llm.py      # 语言模型路由
│   │   │   └── voice.py    # 语音处理路由
│   │   ├── schemas/    # AI服务数据模型
│   │   └── services/   # AI服务业务逻辑
│   │       ├── image_processor.py  # 图像处理服务
│   │       ├── llm_handler.py      # 语言模型服务
│   │       └── voice_processor.py  # 语音处理服务
│   ├── API.md          # AI服务API文档
│   └── requirements.txt # AI服务依赖
├── alembic/            # 数据库迁移
├── configs/            # 配置文件目录
├── data/              # 数据文件目录
├── uploads/           # 上传文件目录
│   └── avatars/      # 用户头像目录
├── static/            # 静态文件目录
│   └── recipe_images/ # 食谱图片目录
├── alembic.ini        # Alembic配置文件
├── api_documentation.json # API文档JSON
├── main.py            # 主入口点
├── .env.example       # 环境变量示例
├── requirements.txt   # 项目依赖
├── setup_env.sh       # 环境设置脚本
├── set_proxy.sh       # 代理设置脚本
└── API.md             # API文档

```

## 核心组件说明

### 1. 应用核心
- `main.py`: 应用程序入口点，负责启动服务
- `app.py`: FastAPI应用程序配置，包含中间件和路由注册
- `database.py`: 数据库连接和会话管理

### 2. 路由模块 (src/routers/)
- `api.py`: 主路由聚合器，组合所有子路由
- `auth.py`: 处理用户认证，包括注册、登录等
- `chat.py`: 处理AI聊天功能，支持文本、语音和图片交互
- `favorites.py`: 管理用户的食谱收藏
- `profile.py`: 管理用户档案，包括基本信息、饮食偏好、运动偏好等
- `recipes.py`: 处理食谱的CRUD操作
- `workout.py`: 管理用户的运动记录

### 3. 数据模型 (src/models/)
- `user.py`: 用户数据模型，存储用户基本信息和认证数据
- `recipe.py`: 食谱数据模型，包含食材、步骤和营养信息
- `favorite.py`: 收藏关系模型
- `chat.py`: 聊天消息模型，存储用户与AI的对话记录
- `nutrition.py`: 营养记录模型，跟踪用户的营养摄入
- `profile.py`: 用户档案模型，存储用户的详细信息和偏好
- `rating.py`: 评分模型，管理用户对食谱的评价
- `workout.py`: 运动记录模型，跟踪用户的运动数据

### 4. 数据验证 (src/schemas/)
- `auth.py`: 认证相关的请求/响应模型
- `chat.py`: 聊天功能的数据模型
- `recipe.py`: 食谱相关的数据验证模型
- `profile.py`: 用户档案的数据模型
- `workout.py`: 运动记录的数据模型
- `favorite.py`: 收藏功能的数据模型
- `user.py`: 用户相关的数据模型
- `responses.py`: 通用响应模型

### 5. 服务层 (src/services/)
- `ai_service_client.py`: AI服务客户端，处理与AI模型的交互
- `recommendation_service.py`: 个性化推荐服务，基于用户偏好生成推荐

### 6. 认证模块 (src/auth/)
- `jwt.py`: JWT令牌的生成和验证

### 7. 中间件 (src/middleware/)
- `rate_limiter.py`: 实现请求频率限制
- `error_handler.py`: 全局错误处理和异常转换
- `version.py`: API版本控制
- `response_handler.py`: 响应格式化和处理

### 8. 工具模块
- `input_processor.py`: 处理和验证用户输入
- `validators.py`: 通用数据验证函数
- `error_handler.py`: 错误处理和异常管理
- `async_handler.py`: 异步操作和任务管理
- `cache_manager.py`: 缓存策略和数据缓存
- `logging_config.py`: 日志配置和管理

### 9. 配置模块 (src/config/)
- `cors.py`: CORS策略配置

### 10. Web界面
- `web_app.py`: Web应用界面实现

## 主要功能

1. 用户管理
   - 用户注册
   - 用户登录
   - 个人资料管理
   - 修改密码
   - 头像上传

2. 食谱管理
   - 食谱创建和编辑
   - 食材和步骤管理
   - 营养成分计算
   - 收藏功能

3. 健康追踪
   - 运动记录
   - 营养摄入统计
   - 健康目标设置

4. AI助手
   - 智能聊天
   - 图片识别
   - 语音交互
   - 个性化建议

## 环境配置

1. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
cp .env.example .env
# 编辑.env文件，填入必要的配置信息
```

4. 运行数据库迁移：
```bash
alembic upgrade head
```

5. 启动服务：
```bash
uvicorn src.main:app --reload
```

## API文档

详细的API文档请参考 [API.md](API.md)

## 开发指南

1. 代码风格
   - 遵循PEP 8规范
   - 使用类型注解
   - 编写详细的文档字符串

2. 错误处理
   - 使用适当的HTTP状态码
   - 提供清晰的错误消息
   - 记录详细的错误日志

3. 安全性
   - 所有敏感信息使用环境变量
   - 实现请求频率限制
   - 使用安全的密码哈希

4. 测试
   - 编写单元测试
   - 进行集成测试
   - 使用测试覆盖率工具

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

[MIT License](LICENSE)
