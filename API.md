# 美食之旅 API 文档

## 基础信息

- 基础URL: `http://your-server:8000/api/v1`
- 所有请求都应该包含 header: `Content-Type: application/json`
- 认证请求需要包含 header: `Authorization: Bearer {token}`

## 认证接口

### 1. 用户注册

```http
POST /auth/register
Content-Type: application/json

{
    "username": "string",
    "email": "user@example.com",
    "password": "string"
}
```

响应:
```json
{
    "id": "string",
    "username": "string",
    "email": "string",
    "access_token": "string"
}
```

### 2. 用户登录

```http
POST /auth/login
Content-Type: application/json

{
    "username": "string",
    "password": "string"
}
```

响应:
```json
{
    "access_token": "string",
    "token_type": "bearer"
}
```

### 3. 刷新令牌

```http
POST /auth/refresh
Authorization: Bearer {token}
```

响应:
```json
{
    "access_token": "string",
    "token_type": "bearer"
}
```

## 用户管理接口

### 1. 获取当前用户信息

```http
GET /users/me
Authorization: Bearer {token}
```

响应:
```json
{
    "id": "string",
    "username": "string",
    "email": "string"
}
```

### 2. 更新用户信息

```http
PUT /users/me
Authorization: Bearer {token}
Content-Type: application/json

{
    "username": "string",
    "email": "string",
    "password": "string"
}
```

响应:
```json
{
    "id": "string",
    "username": "string",
    "email": "string"
}
```

### 3. 删除账号

```http
DELETE /users/me
Authorization: Bearer {token}
```

响应:
```json
{
    "status": "success",
    "message": "账号已删除"
}
```

## 菜谱接口

### 1. 获取菜谱列表

```http
GET /recipes?skip=0&limit=10&category=string&cuisine=string&difficulty=string
Authorization: Bearer {token}
```

响应:
```json
[
    {
        "id": "string",
        "title": "string",
        "description": "string",
        "ingredients": ["string"],
        "steps": ["string"],
        "category": "string",
        "cuisine": "string",
        "difficulty": "string",
        "cooking_time": "integer",
        "author_id": "string",
        "created_at": "string",
        "updated_at": "string"
    }
]
```

### 2. 创建菜谱

```http
POST /recipes
Authorization: Bearer {token}
Content-Type: application/json

{
    "title": "string",
    "description": "string",
    "ingredients": ["string"],
    "steps": ["string"],
    "category": "string",
    "cuisine": "string",
    "difficulty": "string",
    "cooking_time": "integer"
}
```

### 3. 获取菜谱详情

```http
GET /recipes/{recipe_id}
Authorization: Bearer {token}
```

### 4. 更新菜谱

```http
PUT /recipes/{recipe_id}
Authorization: Bearer {token}
Content-Type: application/json

{
    "title": "string",
    "description": "string",
    "ingredients": ["string"],
    "steps": ["string"],
    "category": "string",
    "cuisine": "string",
    "difficulty": "string",
    "cooking_time": "integer"
}
```

### 5. 删除菜谱

```http
DELETE /recipes/{recipe_id}
Authorization: Bearer {token}
```

### 6. 获取推荐菜谱

```http
GET /recipes/recommendations?limit=10
Authorization: Bearer {token}
```

### 7. 搜索菜谱

```http
GET /recipes/search?query=string&skip=0&limit=10
Authorization: Bearer {token}
```

### 8. 食材识别

```http
POST /recipes/ingredient-recognition
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: [图片文件]
```

### 9. 收藏菜谱

```http
POST /recipes/{recipe_id}/favorite
Authorization: Bearer {token}
```

### 10. 取消收藏

```http
DELETE /recipes/{recipe_id}/favorite
Authorization: Bearer {token}
```

### 11. 评分和评论

```http
POST /recipes/{recipe_id}/rating
Authorization: Bearer {token}
Content-Type: application/json

{
    "rating": integer,
    "comment": "string"
}
```

## 用户画像接口

### 1. 获取用户偏好

```http
GET /profile/preferences
Authorization: Bearer {token}
```

### 2. 更新用户偏好

```http
PUT /profile/preferences
Authorization: Bearer {token}
Content-Type: application/json

{
    "favorite_cuisines": ["string"],
    "dietary_restrictions": ["string"],
    "allergies": ["string"]
}
```

### 3. 获取历史记录

```http
GET /profile/history?skip=0&limit=10
Authorization: Bearer {token}
```

### 4. 获取收藏列表

```http
GET /profile/favorites?skip=0&limit=10
Authorization: Bearer {token}
```

## 系统配置接口

### 1. 获取菜品分类

```http
GET /system/categories
Authorization: Bearer {token}
```

### 2. 获取菜系列表

```http
GET /system/cuisines
Authorization: Bearer {token}
```

### 3. 获取难度等级

```http
GET /system/difficulty-levels
Authorization: Bearer {token}
```

## 错误响应

所有接口在发生错误时都会返回以下格式的响应：

```json
{
    "detail": "错误信息描述"
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
- 500: 服务器内部错误

## iOS 集成示例

### Swift 网络层实现

```swift
import Foundation

class APIClient {
    static let baseURL = "http://your-server:8000/api/v1"
    static var token: String?
    
    enum APIError: Error {
        case unauthorized
        case notFound
        case serverError
        case invalidResponse
    }
    
    // 通用请求方法
    static func request<T: Codable>(
        endpoint: String,
        method: String = "GET",
        body: Data? = nil,
        headers: [String: String] = [:]
    ) async throws -> T {
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            throw APIError.invalidResponse
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let token = token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        for (key, value) in headers {
            request.setValue(value, forHTTPHeaderField: key)
        }
        
        if let body = body {
            request.httpBody = body
        }
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        switch httpResponse.statusCode {
        case 200...299:
            return try JSONDecoder().decode(T.self, from: data)
        case 401:
            throw APIError.unauthorized
        case 404:
            throw APIError.notFound
        default:
            throw APIError.serverError
        }
    }
    
    // 登录
    static func login(username: String, password: String) async throws -> String {
        let body = try JSONSerialization.data(withJSONObject: [
            "username": username,
            "password": password
        ])
        
        let response: LoginResponse = try await request(
            endpoint: "/auth/login",
            method: "POST",
            body: body
        )
        
        token = response.access_token
        return response.access_token
    }
    
    // 获取推荐菜谱
    static func getRecipeRecommendations(limit: Int = 10) async throws -> [Recipe] {
        let response: RecipeListResponse = try await request(
            endpoint: "/recipes/recommendations?limit=\(limit)"
        )
        return response.recipes
    }
    
    // 搜索菜谱
    static func searchRecipes(
        query: String,
        skip: Int = 0,
        limit: Int = 10
    ) async throws -> [Recipe] {
        let endpoint = "/recipes/search?query=\(query)&skip=\(skip)&limit=\(limit)"
        let response: RecipeListResponse = try await request(endpoint: endpoint)
        return response.recipes
    }
    
    // 上传图片识别食材
    static func uploadImage(_ imageData: Data) async throws -> IngredientResponse {
        let boundary = UUID().uuidString
        var body = Data()
        
        // 添加图片数据
        body.append("--\(boundary)\r\n")
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"image.jpg\"\r\n")
        body.append("Content-Type: image/jpeg\r\n\r\n")
        body.append(imageData)
        body.append("\r\n--\(boundary)--\r\n")
        
        return try await request(
            endpoint: "/recipes/ingredient-recognition",
            method: "POST",
            body: body,
            headers: [
                "Content-Type": "multipart/form-data; boundary=\(boundary)"
            ]
        )
    }
}

// 响应模型
struct LoginResponse: Codable {
    let access_token: String
    let token_type: String
}

struct Recipe: Codable {
    let id: String
    let title: String
    let description: String
    let ingredients: [String]
    let steps: [String]
    let category: String
    let cuisine: String
    let difficulty: String
    let cooking_time: Int
    let author_id: String
    let created_at: String
    let updated_at: String
}

struct RecipeListResponse: Codable {
    let recipes: [Recipe]
}

struct IngredientResponse: Codable {
    let ingredients: [String]
    let recipe_suggestions: [Recipe]
}
```

## 注意事项

1. 安全性
   - 生产环境必须使用 HTTPS
   - 实现 token 刷新机制
   - 敏感信息加密传输
   - 实现请求签名机制

2. 错误处理
   - 实现完整的错误处理机制
   - 提供清晰的错误信息
   - 记录错误日志

3. 性能优化
   - 实现图片压缩
   - 使用缓存机制
   - 分页加载数据
   - 使用 CDN 加速静态资源

4. 网络状态
   - 实现网络状态检测
   - 离线模式支持
   - 请求重试机制

5. 数据同步
   - 实现增量更新
   - 处理数据冲突
   - 后台同步机制
``` 