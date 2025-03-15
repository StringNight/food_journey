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

### 用户信息自动提取功能

系统现在支持从用户消息中自动提取个人信息并更新用户画像。当用户在对话中提及自己的身高、体重、饮食偏好、健康状况等信息时，系统会自动识别并更新到用户画像中，无需用户手动更新个人资料。

这一功能适用于所有聊天接口，包括：
- 文本聊天 (`POST /chat/stream`)
- 语音聊天 (`POST /chat/voice`)
- 图片聊天 (`POST /chat/image/stream`)

提取的信息类型包括但不限于：
- 身体数据（身高、体重、体脂率等）
- 健康状况
- 饮食偏好和限制
- 过敏信息
- 健身习惯和目标

注意：这些更新是在后台自动进行的，不会在聊天界面中显示给用户。

### 历史消息处理

系统会保留整个对话历史记录并传递给AI模型，这确保了AI可以基于完整的上下文来提供回复。每次发送请求时，前端应包含完整的对话历史，包括所有用户和助手的消息，格式如下：

```json
"messages": [
  {"role": "system", "content": "系统指令..."},
  {"role": "user", "content": "用户第一条消息"},
  {"role": "assistant", "content": "助手第一条回复"},
  {"role": "user", "content": "用户第二条消息"},
  {"role": "assistant", "content": "助手第二条回复"},
  {"role": "user", "content": "当前用户消息"}
]
```

系统会保持消息的原始顺序，确保对话上下文的完整性。

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

## 训练记录API

### 记录训练数据

```
POST /api/v1/profile/exercise
```

记录一次训练数据，包含各组次的详细信息。

**请求体**
```json
{
  "id": "uuid-optional",
  "exercise_name": "硬拉",
  "exercise_type": "力量",
  "sets": [
    {
      "reps": 10,
      "weight": 60.0,
      "duration": null,
      "distance": null
    },
    {
      "reps": 10,
      "weight": 60.0,
      "duration": null,
      "distance": null
    }
  ],
  "calories_burned": 150.5,
  "notes": "今天感觉状态很好",
  "recorded_at": "2024-01-11T15:30:00Z"
}
```

**响应体**
```json
{
  "id": "uuid",
  "user_id": "user-uuid",
  "exercise_name": "硬拉",
  "exercise_type": "力量",
  "sets": [
    {
      "reps": 10,
      "weight": 60.0,
      "duration": null,
      "distance": null
    },
    {
      "reps": 10,
      "weight": 60.0,
      "duration": null,
      "distance": null
    }
  ],
  "calories_burned": 150.5,
  "notes": "今天感觉状态很好",
  "recorded_at": "2024-01-11T15:30:00Z",
  "created_at": "2024-01-11T15:31:22Z",
  "updated_at": "2024-01-11T15:31:22Z"
}
```

### 快速记录多组训练数据

```
POST /api/v1/profile/exercise/multi-sets
```

快速记录多组相同参数的训练数据。适用于记录多组相同重量、相同次数的训练。

**请求体**
```json
{
  "id": "uuid-optional",
  "exercise_name": "硬拉",
  "exercise_type": "力量",
  "num_sets": 3,
  "reps": 10,
  "weight": 60.0,
  "calories_burned": 150.5,
  "notes": "记录3组10次，每组60kg的硬拉",
  "recorded_at": "2024-01-11T15:30:00Z"
}
```

**响应体**
```json
{
  "id": "uuid",
  "user_id": "user-uuid",
  "exercise_name": "硬拉",
  "exercise_type": "力量",
  "sets": [
    {
      "reps": 10,
      "weight": 60.0,
      "duration": null,
      "distance": null
    },
    {
      "reps": 10,
      "weight": 60.0,
      "duration": null,
      "distance": null
    },
    {
      "reps": 10,
      "weight": 60.0,
      "duration": null,
      "distance": null
    }
  ],
  "calories_burned": 150.5,
  "notes": "记录3组10次，每组60kg的硬拉",
  "recorded_at": "2024-01-11T15:30:00Z",
  "created_at": "2024-01-11T15:31:22Z",
  "updated_at": "2024-01-11T15:31:22Z"
}
```

参数说明：
- `id`: 可选，记录ID，如不提供将自动生成
- `exercise_name`: 必填，训练名称
- `exercise_type`: 必填，训练类型，可选值：力量、有氧、拉伸、其他
- `num_sets`: 必填，要记录的组数
- `reps`: 必填，每组重复次数
- `weight`: 可选，重量（千克）
- `duration`: 可选，持续时间（秒）
- `distance`: 可选，距离（米）
- `calories_burned`: 可选，消耗卡路里
- `notes`: 可选，备注
- `recorded_at`: 可选，记录时间，如不提供将使用当前时间

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

## 用户档案服务 (Profile Service)

### 获取用户档案

```
GET /profile
```

**响应**
```json
{
    "schema_version": "1.0",
    "user_profile": {
        "id": "string",
        "username": "string",
        "nickname": "string",
        "avatar_url": "string",
        "birth_date": "2023-01-01",
        "age": 30,
        "gender": "男",
        "created_at": "2023-01-01T12:00:00Z",
        "updated_at": "2023-01-01T12:00:00Z"
    },
    "health_profile": {
        "height": 175,
        "weight": 70,
        "body_fat_percentage": 20,
        "muscle_mass": 55,
        "bmr": 1500,
        "tdee": 2200,
        "health_conditions": ["健康"],
        "bmi": 22.9,
        "water_ratio": 60
    },
    "diet_profile": {
        "cooking_skill_level": "中级",
        "favorite_cuisines": ["中餐", "日料"],
        "dietary_restrictions": [],
        "allergies": [],
        "nutrition_goals": {
            "protein": 120,
            "carbs": 250,
            "fat": 60
        },
        "calorie_preference": 2000,
        "eating_habits": "规律三餐",
        "diet_goal": "保持体重"
    },
    "fitness_profile": {
        "fitness_level": "中级",
        "exercise_frequency": 3,
        "preferred_exercises": ["力量训练", "跑步"],
        "fitness_goals": ["增肌", "提高耐力"],
        "short_term_goals": ["增加5kg肌肉"],
        "long_term_goals": ["保持健康"],
        "goal_progress": 35,
        "training_type": "力量训练",
        "training_progress": 40,
        "muscle_group_analysis": {
            "胸肌": 30,
            "背肌": 45,
            "腿部": 35
        },
        "sleep_duration": 7.5,
        "deep_sleep_percentage": 25,
        "fatigue_score": 2,
        "recovery_activities": ["拉伸", "按摩"],
        "performance_metrics": {
            "卧推": 80,
            "深蹲": 120
        },
        "exercise_history": [],
        "training_time_preference": "早晨",
        "equipment_preferences": ["哑铃", "杠铃"]
    },
    "extended_attributes": {}
}
```

### 更新用户基本信息

```
PUT /profile/basic
```

**请求体**
```json
{
    "birth_date": "1990-01-01",
    "gender": "男",
    "height": 175,
    "weight": 70,
    "body_fat_percentage": 20,
    "muscle_mass": 55,
    "health_conditions": ["健康"]
}
```

**响应**
```json
{
    "schema_version": "1.0",
    "message": "基础信息更新成功",
    "updated_fields": ["birth_date", "gender", "height", "weight", "body_fat_percentage", "muscle_mass", "health_conditions"]
}
```

### 更新饮食偏好

```
PUT /profile/diet
```

**请求体**
```json
{
    "cooking_skill_level": "中级",
    "favorite_cuisines": ["中餐", "日料"],
    "dietary_restrictions": [],
    "allergies": [],
    "nutrition_goals": {
        "protein": 120,
        "carbs": 250,
        "fat": 60
    },
    "calorie_preference": 2000,
    "extended_attributes": {
        "diet_advice": "增加蛋白质摄入，减少糖分摄入"
    }
}
```

**响应**
```json
{
    "schema_version": "1.0",
    "message": "饮食偏好更新成功",
    "updated_fields": ["cooking_skill_level", "favorite_cuisines", "nutrition_goals", "calorie_preference", "extended_attributes.diet_advice"]
}
```

### 记录餐食

```
POST /profile/meal
```

**请求体**
```json
{
    "meal_type": "早餐",
    "food_items": [
        {
            "food_name": "全麦面包",
            "portion": 100,
            "calories": 250,
            "protein": 8,
            "carbs": 45,
            "fat": 3
        },
        {
            "food_name": "鸡蛋",
            "portion": 50,
            "calories": 75,
            "protein": 6,
            "carbs": 1,
            "fat": 5
        }
    ],
    "total_calories": 325,
    "notes": "早餐记录",
    "recorded_at": "2023-01-01T08:00:00Z"
}
```

**响应**
```json
{
    "id": "string",
    "user_id": "string",
    "meal_type": "早餐",
    "food_items": [
        {
            "food_name": "全麦面包",
            "portion": 100,
            "calories": 250,
            "protein": 8,
            "carbs": 45,
            "fat": 3
        },
        {
            "food_name": "鸡蛋",
            "portion": 50,
            "calories": 75,
            "protein": 6,
            "carbs": 1,
            "fat": 5
        }
    ],
    "total_calories": 325,
    "notes": "早餐记录",
    "recorded_at": "2023-01-01T08:00:00Z",
    "created_at": "2023-01-01T08:05:00Z",
    "updated_at": "2023-01-01T08:05:00Z"
}
``` 