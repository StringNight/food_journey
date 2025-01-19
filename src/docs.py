"""API文档配置模块

提供API文档的配置和自定义设置
"""

from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI

def custom_openapi(app: FastAPI):
    """自定义OpenAPI文档配置
    
    Args:
        app: FastAPI应用实例
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="美食之旅 API",
        version="1.0.0",
        description="""
# 美食之旅后端API文档

## 功能概述

### 用户管理
- 用户注册和登录
- 个人信息管理
- JWT token认证
- 账户安全保护

### 菜谱管理
- 创建和编辑菜谱
- 搜索和浏览菜谱
- 菜谱评分和评论

### 收藏功能
- 收藏/取消收藏菜谱
- 查看收藏列表

## 使用说明
1. 所有需要认证的接口都需要在请求头中携带JWT token
2. Token格式：`Authorization: Bearer <token>`
3. 分页接口默认每页20条数据
4. 所有时间相关的字段都使用ISO 8601格式
5. 接口调用频率限制：每分钟60次
6. 账户锁定策略：连续5次登录失败将锁定15分钟

## 错误处理
- 400: 请求参数错误
- 401: 未认证或token无效
- 403: 权限不足或账户被锁定
- 404: 资源不存在
- 422: 请求数据验证失败
- 429: 请求频率超限
- 500: 服务器内部错误
        """,
        routes=app.routes,
    )
    
    # 添加安全配置
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
        
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT认证token，有效期30分钟"
        }
    }
    
    # 添加全局安全要求
    openapi_schema["security"] = [{"bearerAuth": []}]
    
    # 自定义标签说明
    openapi_schema["tags"] = [
        {
            "name": "认证",
            "description": """
用户认证相关接口，包括：
- 用户注册：创建新用户账户
- 用户登录：支持表单和JSON两种方式
- 刷新token：获取新的访问令牌
- 修改密码：更新用户密码
- 上传头像：更新用户头像
- 删除账户：注销用户账户

安全特性：
- 密码加密存储
- 登录失败次数限制
- 账户自动锁定保护
- 访问频率限制
"""
        },
        {
            "name": "用户档案",
            "description": "用户个人信息管理接口，包括：获取个人信息、更新个人信息、修改密码"
        },
        {
            "name": "菜谱",
            "description": "菜谱管理相关接口，包括：创建菜谱、更新菜谱、删除菜谱、搜索菜谱、菜谱评分"
        },
        {
            "name": "收藏",
            "description": "菜谱收藏相关接口，包括：收藏菜谱、取消收藏、获取收藏列表"
        }
    ]
    
    # 添加通用响应
    if "responses" not in openapi_schema["components"]:
        openapi_schema["components"]["responses"] = {}
        
    openapi_schema["components"]["responses"].update({
        "UnauthorizedError": {
            "description": "未认证或token无效",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "example": "Could not validate credentials"
                            }
                        }
                    }
                }
            }
        },
        "NotFoundError": {
            "description": "请求的资源不存在",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "example": "Resource not found"
                            }
                        }
                    }
                }
            }
        },
        "ValidationError": {
            "description": "请求数据验证失败",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "loc": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "msg": {"type": "string"},
                                        "type": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "RateLimitError": {
            "description": "请求频率超过限制",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "example": "Too many requests"
                            }
                        }
                    }
                }
            }
        },
        "AccountLockedError": {
            "description": "账户被锁定",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "example": "Account is locked, please try again later"
                            }
                        }
                    }
                }
            }
        }
    })
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema 