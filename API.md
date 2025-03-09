# 美食之旅 API 文档

## 基础信息

- 基础URL: `/api/v1`
- 所有请求和响应均使用 JSON 格式
- 所有需要认证的接口都需要在请求头中包含 `Authorization: Bearer <token>`

## 认证服务 (Auth Service)

### 用户注册

```
POST /auth/register
```

**请求体**
```json
{
    "username": "string",
    "password": "string"
}
```

**响应**
```json
{
    "id": "string",
    "username": "string",
    "access_token": "string",
    "token_type": "bearer"
}
```

### 用户登录

```
POST /auth/login/json
```

**请求体**
```json
{
    "username": "string",
    "password": "string"
}
```

**响应**
```json
{
    "access_token": "string",
    "token_type": "bearer",
    "user": {
        "id": "string",
        "username": "string",
        "created_at": "2024-01-11T00:00:00",
        "avatar_url": "string"
    }
}
```

### 修改密码

```
POST /auth/change-password
```

**请求体**
```json
{
    "current_password": "string",
    "new_password": "string"
}
```

**响应**
```json
{
    "message": "密码修改成功"
}
```

### 上传头像

```
POST /auth/avatar
```

**请求体**
```
multipart/form-data
file: 图片文件
```

**响应**
```json
{
    "avatar_url": "string"
}
```

### 刷新令牌

```
POST /auth/refresh
```

**响应**
```json
{
    "access_token": "string",
    "token_type": "bearer"
}
```

## 用户服务 (User Service)

### 获取用户档案

```
GET /users/{user_id}/profile
```

**响应**
```json
{
    "id": "string",
    "user_id": "string",
    "avatar_url": "string",
    "birth_date": "2024-01-11",
    "gender": "string",
    "height": 170.0,
    "weight": 65.0,
    "body_fat_percentage": 20.0,
    "muscle_mass": 50.0,
    "bmr": 1500,
    "tdee": 2000,
    "health_conditions": ["高血压", "糖尿病"],
    "health_goals": ["减重", "增肌"],
    "cooking_skill_level": "初级",
    "favorite_cuisines": ["中餐", "日料"],
    "dietary_restrictions": ["无麸质", "素食"],
    "allergies": ["花生", "海鲜"],
    "calorie_preference": 2000,
    "nutrition_goals": {
        "protein": 150,
        "carbs": 200,
        "fat": 60
    },
    "fitness_level": "中级",
    "exercise_frequency": 3,
    "preferred_exercises": ["跑步", "力量训练"],
    "fitness_goals": ["增肌", "提高耐力"],
    "extended_attributes": {},
    "created_at": "2024-01-11T00:00:00",
    "updated_at": "2024-01-11T00:00:00"
}
```

### 更新用户档案

```
PUT /users/{user_id}/profile
```

**请求体**
```json
{
    "avatar_url": "string",
    "birth_date": "2024-01-11",
    "gender": "string",
    "height": 170.0,
    "weight": 65.0,
    "body_fat_percentage": 20.0,
    "muscle_mass": 50.0,
    "health_conditions": ["高血压", "糖尿病"],
    "health_goals": ["减重", "增肌"],
    "cooking_skill_level": "初级",
    "favorite_cuisines": ["中餐", "日料"],
    "dietary_restrictions": ["无麸质", "素食"],
    "allergies": ["花生", "海鲜"],
    "calorie_preference": 2000,
    "nutrition_goals": {
        "protein": 150,
        "carbs": 200,
        "fat": 60
    },
    "fitness_level": "中级",
    "exercise_frequency": 3,
    "preferred_exercises": ["跑步", "力量训练"],
    "fitness_goals": ["增肌", "提高耐力"],
    "extended_attributes": {}
}
```

**响应**
```json
{
    "success": true,
    "message": "用户档案更新成功"
}
```

### 更新用户偏好

```
PUT /users/{user_id}/preferences
```

**请求体**
```json
{
    "favorite_cuisines": ["中餐", "日料"],
    "dietary_restrictions": ["无麸质", "素食"]
}
```

**响应**
```json
{
    "success": true
}
```

## 菜谱服务 (Recipe Service)

### 创建菜谱

```
POST /recipes
```

**请求体**
```json
{
    "title": "红烧肉",
    "ingredients": [
        {
            "name": "五花肉",
            "amount": 500,
            "unit": "g"
        }
    ],
    "steps": [
        {
            "step": 1,
            "description": "将五花肉切块"
        }
    ],
    "cooking_time": 60,
    "difficulty": "中等"
}
```

**响应**
```json
{
    "recipe_id": "string"
}
```

### 获取菜谱

```
GET /recipes/{recipe_id}
```

**响应**
```json
{
    "id": "string",
    "title": "string",
    "ingredients": [
        {
            "name": "string",
            "amount": 0,
            "unit": "string"
        }
    ],
    "steps": [
        {
            "step": 0,
            "description": "string"
        }
    ],
    "cooking_time": 0,
    "difficulty": "string",
    "ratings": [
        {
            "rating": 0,
            "comment": "string"
        }
    ],
    "average_rating": 0
}
```

### 评分菜谱

```
POST /recipes/{recipe_id}/ratings
```

**请求体**
```json
{
    "rating": 5,
    "comment": "非常好吃！"
}
```

**响应**
```json
{
    "success": true
}
```

## AI 服务 (AI Service)

### 生成菜谱

```
POST /ai/generate-recipe
```

**请求体**
```json
{
    "text": "想做一道简单的家常菜",
    "voice_file": "base64编码的音频文件",
    "image_file": "base64编码的图片文件"
}
```

**响应**
```json
{
    "response": "string"
}
```

## 流式聊天接口

### 接口说明

URL: `/chat_stream`

此接口支持流式返回，通过异步生成器逐步返回聊天回复文本块。前端调用时请确保开启流式（stream）模式，以实时接收返回的文本更新。

### 请求参数

```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    // 其他对话历史
  ],
  "model": "qwen2.5:14b",
  "max_tokens": 2000,
  "user_profile": { /* 用户画像，可选 */ }
}
```

### 返回值

返回值是一个异步文本块生成器，每个返回块为如下格式的部分回复：

```json
{
  "role": "assistant",
  "content": "聊天回复的部分文本..."
}
```

### 示例代码

```python
from gradio_client import Client

client = Client("https://1ba902d825722a9416.gradio.live/")
result = client.predict(
  messages=[{"role": "system", "content": "You are a helpful assistant. You will talk like a pirate."}],
  model="qwen2.5:14b",
  max_tokens=2000,
  api_name="/chat_stream"
)
print(result)
```

说明: 请确保前端在调用此接口时启用stream模式，以支持流式返回。

## 错误处理

### 验证错误

当请求验证失败时（例如，用户注册时密码不符合要求），API会返回422状态码和包含详细错误信息的响应。错误响应格式如下：

```json
{
  "detail": "输入数据验证失败",
  "type": "validation_error",
  "errors": [
    {
      "field": "password",
      "field_path": "body.password",
      "message": "密码必须包含至少一个大写字母",
      "type": "value_error"
    }
  ]
}
```

前端应处理这些错误并显示具体的错误消息给用户，而不是显示通用的错误信息。

### 常见验证错误

用户注册/修改密码时可能遇到的常见验证错误：

- 用户名相关：
  - "用户名只能包含字母、数字、下划线和连字符"
  - "用户名长度必须在3到32个字符之间"
  - "用户名已存在"

- 密码相关：
  - "密码长度必须在8到64个字符之间"
  - "密码必须包含至少一个大写字母"
  - "密码必须包含至少一个小写字母"
  - "密码必须包含至少一个数字"
  - "密码必须包含至少一个特殊字符"

### 其他错误类型

- 400 Bad Request: 请求参数错误
- 401 Unauthorized: 未认证或认证失败
- 403 Forbidden: 账户被锁定或没有权限
- 429 Too Many Requests: 请求频率超过限制
- 500 Internal Server Error: 服务器内部错误 