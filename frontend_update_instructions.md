# 前端更新说明：处理后端详细错误信息

我们已经更新了后端的错误响应格式，使其能够返回更详细的验证错误信息。为了在前端正确显示这些错误信息，需要进行以下更新：

## 已完成的修改

1. 更新了 `AuthModels.swift` 中的 `ErrorResponse` 模型，使其能够解析新的错误响应格式：
   - 添加了 `type` 和 `errors` 字段
   - 添加了 `ValidationError` 结构体来解析具体错误信息

2. 更新了 `NetworkService.swift` 中的错误处理逻辑：
   - 添加了对 422 验证错误的专门处理
   - 添加了 `NetworkError.LocalizedError` 扩展以提供本地化错误描述

## 如何应用更新

1. 打开 Xcode 项目，使用 Cursor 生成的代码更新上述文件
2. 清理并重新构建项目 (Product > Clean Build Folder，然后 Product > Build)
3. 运行应用程序并测试注册功能

## 测试建议

测试以下场景，确保错误信息正确显示：

1. 使用不符合规则的密码注册（例如缺少大写字母、小写字母、数字或特殊字符）
2. 使用已存在的用户名注册
3. 使用不符合规则的用户名注册（例如包含特殊字符）

## 后端错误格式示例

当验证失败时，后端现在会返回以下格式的错误：

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

## 联系方式

如果在应用更新时遇到任何问题，请联系后端开发团队。
