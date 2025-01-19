from fastapi.openapi.utils import get_openapi
from typing import Dict, Any

def custom_openapi(app) -> Dict[str, Any]:
    """生成自定义OpenAPI文档
    
    Args:
        app: FastAPI应用实例
        
    Returns:
        Dict[str, Any]: OpenAPI文档
    """
    if app.openapi_schema:
        return app.openapi_schema
        
    openapi_schema = get_openapi(
        title="美食之旅 API",
        version="1.0.0",
        description="""
# 美食之旅 API 文档

## 基础信息
- 基础URL: `http://your-server:8000/api/v1`
- 所有请求都应该包含 header: `Content-Type: application/json`
- 认证请求需要包含 header: `Authorization: Bearer {token}`

## 认证机制
- 使用 JWT (JSON Web Token) 进行认证
- 访问令牌有效期为7天
- 支持令牌刷新机制

## 错误处理
所有接口在发生错误时都会返回统一格式的响应：
```json
{
    "detail": "错误信息描述",
    "type": "错误类型"
}
```

常见的 HTTP 状态码：
- 200: 请求成功
- 201: 创建成功
- 400: 请求参数错误
- 401: 未认证
- 403: 无权限
- 404: 资源不存在
- 422: 参数验证失败
- 429: 请求过于频繁
- 500: 服务器内部错误

## 版本控制
- 在URL中使用版本号: `/api/v1/`
- 在请求头中使用 `X-API-Version`
- 响应头中会返回 `X-API-Version`

## 速率限制
- 全局限制：每分钟60个请求
- 特定接口可能有独立的限制
- 超出限制时返回429状态码

## 聊天接口说明

### 文本聊天
- POST `/api/v1/chat/text`
- 发送文本消息与AI助手对话
- 支持的模型：qwen2.5:14b
- 最大消息长度：1000字符

### 流式文本聊天
- POST `/api/v1/chat/text/stream`
- 使用Server-Sent Events (SSE)进行实时对话
- 响应格式：`data: {chunk}\n\n`
- 需要使用EventSource或类似工具接收响应

### 语音聊天
- POST `/api/v1/chat/voice`
- 支持的音频格式：wav, mp3
- 最大文件大小：10MB
- 返回语音转写文本和AI回复

### 食物识别
- POST `/api/v1/chat/food`
- 支持的图片格式：jpeg, png, gif
- 最大文件大小：10MB
- 返回识别到的食物列表和营养信息

## 最佳实践
1. 总是检查响应状态码
2. 实现错误重试机制
3. 使用HTTPS进行安全传输
4. 正确处理令牌过期情况
5. 流式接口建议实现断线重连机制
        """,
        routes=app.routes,
    )
    
    # 添加安全定义
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "输入您的访问令牌"
        }
    }
    
    # 添加全局安全要求
    openapi_schema["security"] = [{"bearerAuth": []}]
    
    # 添加标签描述
    openapi_schema["tags"] = [
        {
            "name": "认证",
            "description": "用户认证相关接口，包括注册、登录、重置密码等"
        },
        {
            "name": "用户档案",
            "description": "用户画像相关接口，包括偏好设置、饮食限制等"
        },
        {
            "name": "聊天",
            "description": """与AI助手交互的接口，支持：
- 文本聊天（普通/流式）
- 语音转写和对话
- 食物图片识别"""
        }
    ]
    
    # 添加响应示例
    chat_examples = {
        "/api/v1/chat/text": {
            "post": {
                "request": {
                    "message": "请推荐一道简单的家常菜"
                },
                "response": {
                    "schema_version": "1.0",
                    "message": "我建议你尝试制作西红柿炒鸡蛋，这是一道非常经典的家常菜...",
                    "created_at": "2024-03-15T10:30:00Z"
                }
            }
        },
        "/api/v1/chat/voice": {
            "post": {
                "response": {
                    "schema_version": "1.0",
                    "message": "根据你的语音内容，我建议...",
                    "voice_url": "https://example.com/voices/123.wav",
                    "transcribed_text": "请问这道菜怎么做",
                    "created_at": "2024-03-15T10:30:00Z"
                }
            }
        },
        "/api/v1/chat/food": {
            "post": {
                "response": {
                    "schema_version": "1.0",
                    "message": "我识别到以下食物：\n- 西红柿炒鸡蛋\n- 青菜",
                    "image_url": "https://example.com/images/123.jpg",
                    "food_items": [
                        {
                            "name": "西红柿炒鸡蛋",
                            "confidence": 0.95
                        },
                        {
                            "name": "青菜",
                            "confidence": 0.88
                        }
                    ],
                    "created_at": "2024-03-15T10:30:00Z"
                }
            }
        }
    }
    
    for path, methods in chat_examples.items():
        if path in openapi_schema["paths"]:
            for method, example in methods.items():
                if method in openapi_schema["paths"][path]:
                    if "requestBody" in openapi_schema["paths"][path][method]:
                        openapi_schema["paths"][path][method]["requestBody"]["content"]["application/json"]["example"] = example["request"]
                    if "responses" in openapi_schema["paths"][path][method]:
                        for response in openapi_schema["paths"][path][method]["responses"].values():
                            if "content" in response:
                                response["content"]["application/json"]["example"] = example["response"]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema 