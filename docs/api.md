## 更新用户健身偏好

```
PUT /profile/fitness
```

更新用户的健身偏好和健康数据。

### 请求体

```json
{
  "fitness_level": "intermediate",
  "exercise_frequency": "3-5_times_week",
  "preferred_exercises": ["跑步", "力量训练", "瑜伽"],
  "fitness_goals": ["减脂", "增肌", "提高耐力"],
  "short_term_goals": ["一周跑步3次", "每天摄入150g蛋白质"],
  "long_term_goals": ["体脂率降至15%", "跑完全马"],
  "goal_progress": 65.5,
  "training_type": "力量训练",
  "training_progress": 75.0,
  "muscle_group_analysis": {
    "胸部": "进步显著",
    "背部": "需要加强",
    "腿部": "有所提升"
  },
  "sleep_duration": 7.5,
  "deep_sleep_percentage": 25.5,
  "fatigue_score": 3,
  "recovery_activities": ["按摩", "拉伸", "冷水浴"],
  "extended_attributes": {
    "recovery_advice": "建议增加柔韧性训练改善恢复质量",
    "custom_field": "自定义值"
  }
}
```

| 字段名 | 类型 | 必填 | 描述 |
| --- | --- | --- | --- |
| fitness_level | string | 否 | 健身水平：初级(beginner)、中级(intermediate)、高级(advanced) |
| exercise_frequency | string | 否 | 锻炼频率：不规律(irregular)、每周1-2次(1-2_times_week)、每周3-5次(3-5_times_week)、每天(daily) |
| preferred_exercises | array | 否 | 偏好的锻炼方式列表 |
| fitness_goals | array | 否 | 健身目标列表 |
| short_term_goals | array | 否 | 短期健身目标列表 |
| long_term_goals | array | 否 | 长期健身目标列表 |
| goal_progress | number | 否 | 目标完成进度百分比(0-100) |
| training_type | string | 否 | 训练类型：如力量训练、有氧训练、柔韧性训练等 |
| training_progress | number | 否 | 训练进度百分比(0-100) |
| muscle_group_analysis | object | 否 | 肌肉群训练分析，键为肌肉群名称，值为分析描述 |
| sleep_duration | number | 否 | 每晚睡眠时长(小时) |
| deep_sleep_percentage | number | 否 | 深度睡眠百分比(0-100) |
| fatigue_score | integer | 否 | 疲劳感评分(1-5)，1表示极低疲劳，5表示极高疲劳 |
| recovery_activities | array | 否 | 恢复活动列表 |
| extended_attributes | object | 否 | 扩展属性，可存储自定义字段 |

### 响应

```json
{
  "schema_version": "1.0",
  "message": "更新用户健身偏好成功",
  "updated_fields": ["fitness_level", "preferred_exercises", "sleep_duration"]
}
```

| 字段名 | 类型 | 描述 |
| --- | --- | --- |
| schema_version | string | API模式版本 |
| message | string | 响应消息 |
| updated_fields | array | 已更新的字段列表 |

### 错误响应

```json
{
  "detail": "更新用户健身偏好失败: 数据验证错误"
}
```

### 注意事项

1. 列表类型字段(如preferred_exercises、fitness_goals等)会与用户现有数据合并并去重
2. 字典类型字段(如muscle_group_analysis、extended_attributes)会更新现有数据而非覆盖
3. 未明确定义的字段会自动存储在extended_attributes中
4. 睡眠和恢复相关数据会存储在专用字段中以便后续分析 