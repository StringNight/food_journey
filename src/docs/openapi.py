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

## 用户画像管理
### 获取用户画像
GET `/api/v1/profile`
获取用户的完整画像信息，包括：
  - 基本信息：用户ID, 性别, 年龄, 昵称, 出生日期等
  - 健康信息：身高(cm), 体重(kg), 体脂率(%), 肌肉含量, 基础代谢率, 每日能量消耗, BMI, 身体水分比例, 健康状况, 健康目标
  - 饮食偏好：烹饪技能水平, 喜好菜系, 饮食限制, 食物过敏, 卡路里偏好, 营养目标, 饮食习惯, 饮食目标
  - 健身信息：健身水平, 每周运动频率, 偏好运动类型, 健身目标, 短期与长期健身目标, 目标进度, 训练类型, 训练进度, 肌肉群分析, 每晚睡眠时长, 深度睡眠比例, 疲劳感评分, 恢复性活动, 运动表现指标, 运动历史记录, 训练时间偏好, 设备偏好
  - 扩展属性：其他未分类的个性化设置

### 更新用户画像
PUT `/api/v1/profile/basic` - 更新用户的基本信息和健康数据（如性别、年龄、身高、体重等）
PUT `/api/v1/profile/diet` - 更新用户的饮食偏好（如烹饪水平、喜好菜系、饮食限制等）
PUT `/api/v1/profile/fitness` - 更新用户的健身习惯和目标（如运动频率、健身目标、睡眠数据等）

### 健康数据统计
- GET `/api/v1/profile/stats`
- 获取用户的健康数据统计，包括：
  - 身体指标趋势
  - 营养摄入总结
  - 运动情况总结

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
- 支持的模型：deepseek-r1:14b
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
            "description": "用户认证相关接口，包括注册、登录等"
        },
        {
            "name": "用户档案",
            "description": """用户画像相关接口，包括：
- 获取完整用户画像
- 更新基本信息和健康数据
- 更新饮食偏好（烹饪水平、喜好菜系等）
- 更新健身偏好（运动水平、运动频率等）
- 获取健康数据统计"""
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
    profile_examples = {
        "/api/v1/profile": {
            "get": {
                "response": {
                    "schema_version": "1.0",
                    "user_profile": {
                        "id": "user-123",
                        "username": "test_user",
                        "avatar_url": "https://example.com/avatar.jpg",
                        "birth_date": "1990-01-01",
                        "gender": "男",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-03-15T10:30:00Z"
                    },
                    "health_profile": {
                        "height": 175,
                        "weight": 70,
                        "body_fat_percentage": 20,
                        "muscle_mass": 35,
                        "bmr": 1600,
                        "tdee": 2200,
                        "health_conditions": ["轻度过敏"]
                    },
                    "diet_profile": {
                        "cooking_skill_level": "中级",
                        "favorite_cuisines": ["川菜", "粤菜"],
                        "dietary_restrictions": ["少油", "少盐"],
                        "allergies": ["海鲜"],
                        "nutrition_goals": {
                            "protein": 120,
                            "carbs": 250,
                            "fat": 60
                        }
                    },
                    "fitness_profile": {
                        "fitness_level": "中级",
                        "exercise_frequency": 3,
                        "preferred_exercises": ["力量训练", "跑步"],
                        "fitness_goals": ["增肌", "提高耐力"]
                    }
                }
            }
        },
        "/api/v1/profile/basic": {
            "put": {
                "request": {
                    "birth_date": "1990-01-01",
                    "gender": "男",
                    "height": 175,
                    "weight": 70,
                    "body_fat_percentage": 20,
                    "muscle_mass": 35,
                    "bmr": 1600,
                    "tdee": 2200,
                    "health_conditions": ["轻度过敏"]
                },
                "response": {
                    "schema_version": "1.0",
                    "message": "基础信息更新成功",
                    "updated_fields": [
                        "birth_date",
                        "gender",
                        "height",
                        "weight",
                        "body_fat_percentage",
                        "muscle_mass",
                        "bmr",
                        "tdee",
                        "health_conditions"
                    ]
                }
            }
        },
        "/api/v1/profile/diet": {
            "put": {
                "request": {
                    "cooking_skill_level": "中级",
                    "favorite_cuisines": ["川菜", "粤菜"],
                    "dietary_restrictions": ["少油", "少盐"],
                    "allergies": ["海鲜"],
                    "calorie_preference": 2000,
                    "nutrition_goals": {
                        "protein": 120,
                        "carbs": 250,
                        "fat": 60
                    }
                },
                "response": {
                    "schema_version": "1.0",
                    "message": "饮食偏好更新成功",
                    "updated_fields": [
                        "cooking_skill_level",
                        "favorite_cuisines",
                        "dietary_restrictions",
                        "allergies",
                        "calorie_preference",
                        "nutrition_goals"
                    ]
                }
            }
        },
        "/api/v1/profile/fitness": {
            "put": {
                "request": {
                    "fitness_level": "中级",
                    "exercise_frequency": 3,
                    "preferred_exercises": ["力量训练", "跑步"],
                    "fitness_goals": ["增肌", "提高耐力"]
                },
                "response": {
                    "schema_version": "1.0",
                    "message": "运动偏好更新成功",
                    "updated_fields": [
                        "fitness_level",
                        "exercise_frequency",
                        "preferred_exercises",
                        "fitness_goals"
                    ]
                }
            }
        },
        "/api/v1/profile/stats": {
            "get": {
                "response": {
                    "schema_version": "1.0",
                    "period": "2024-01-01/2024-03-15",
                    "body_metrics_trend": {
                        "weight": [70, 69.5, 69],
                        "body_fat": [20, 19.5, 19],
                        "muscle_mass": [35, 35.5, 36]
                    },
                    "nutrition_summary": {
                        "average_daily_calories": 2200,
                        "average_macros": {
                            "protein": 110,
                            "carbs": 240,
                            "fat": 55
                        },
                        "meal_patterns": {
                            "most_common_breakfast": ["燕麦", "鸡蛋"],
                            "most_common_cuisines": ["川菜", "粤菜"]
                        }
                    },
                    "fitness_summary": {
                        "total_workouts": 24,
                        "total_duration": 1440,
                        "total_calories_burned": 12000,
                        "exercise_distribution": {
                            "strength": 40,
                            "cardio": 45,
                            "flexibility": 15
                        },
                        "strength_progress": {
                            "bench_press": [50, 52.5, 55],
                            "squat": [70, 75, 77.5]
                        }
                    }
                }
            }
        }
    }
    
    chat_examples = {
        "/api/v1/chat/stream": {
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
        "/api/v1/chat/image/stream": {
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
    
    # 合并所有示例
    examples = {**profile_examples, **chat_examples}
    
    # 添加示例到OpenAPI文档
    for path, methods in examples.items():
        if path in openapi_schema["paths"]:
            for method, example in methods.items():
                if method in openapi_schema["paths"][path]:
                    if "requestBody" in openapi_schema["paths"][path][method] and "request" in example:
                        openapi_schema["paths"][path][method]["requestBody"]["content"]["application/json"]["example"] = example["request"]
                    if "responses" in openapi_schema["paths"][path][method] and "response" in example:
                        for response in openapi_schema["paths"][path][method]["responses"].values():
                            if "content" in response:
                                response["content"]["application/json"]["example"] = example["response"]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema 