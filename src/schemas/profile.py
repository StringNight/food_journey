from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Optional, Any
from datetime import datetime, date

class HealthProfile(BaseModel):
    """健康档案模型"""
    height: Optional[float] = Field(None, description="身高（厘米）", ge=0, le=300)
    weight: Optional[float] = Field(None, description="体重（千克）", ge=0, le=500)
    body_fat_percentage: Optional[float] = Field(None, description="体脂率（%）", ge=0, le=100)
    muscle_mass: Optional[float] = Field(None, description="肌肉量（千克）", ge=0, le=200)
    bmr: Optional[int] = Field(None, description="基础代谢率（卡路里）", ge=0)
    tdee: Optional[int] = Field(None, description="每日总能量消耗（卡路里）", ge=0)
    health_conditions: Optional[List[str]] = Field(None, description="健康状况")
    bmi: Optional[float] = Field(None, description="体重指数（BMI）", ge=0)
    water_ratio: Optional[float] = Field(None, description="身体水分比例（%）", ge=0, le=100)

class DietProfile(BaseModel):
    """饮食档案模型"""
    cooking_skill_level: Optional[str] = Field(
        None, 
        description="烹饪技能水平",
        pattern="^(初级|中级|高级)$"
    )
    favorite_cuisines: Optional[List[str]] = Field(None, description="喜好的菜系")
    dietary_restrictions: Optional[List[str]] = Field(None, description="饮食限制")
    allergies: Optional[List[str]] = Field(None, description="食物过敏")
    nutrition_goals: Optional[Dict] = Field(None, description="营养目标")
    calorie_preference: Optional[int] = Field(None, description="每日卡路里目标", ge=0)
    eating_habits: Optional[str] = Field(None, description="饮食习惯，例如是否有规律进餐，是否吃快餐等")
    diet_goal: Optional[str] = Field(None, description="饮食目标，例如每日摄入2000卡目标，蛋白质摄入100g")

class FitnessProfile(BaseModel):
    """健身档案模型"""
    fitness_level: Optional[str] = Field(
        None, 
        description="健身水平",
        pattern="^(初级|中级|高级)$"
    )
    exercise_frequency: Optional[int] = Field(
        None, 
        description="每周运动频率",
        ge=0,
        le=7
    )
    preferred_exercises: Optional[List[str]] = Field(None, description="偏好的运动类型")
    fitness_goals: Optional[List[str]] = Field(None, description="健身目标")
    short_term_goals: Optional[List[str]] = Field(None, description="短期健身目标，例如增肌5kg，体脂降到15%")
    long_term_goals: Optional[List[str]] = Field(None, description="长期健身目标，例如保持健康，提高运动表现")
    goal_progress: Optional[float] = Field(None, description="目标进度百分比", ge=0, le=100)
    training_type: Optional[str] = Field(None, description="训练类型，如力量训练、跑步、有氧运动等")
    training_progress: Optional[float] = Field(None, description="训练进度（百分比）", ge=0, le=100)
    muscle_group_analysis: Optional[Dict[str, Any]] = Field(None, description="肌肉群分析，记录训练中涉及的肌肉群")
    sleep_duration: Optional[float] = Field(None, description="每晚睡眠时长（小时）", ge=0)
    deep_sleep_percentage: Optional[float] = Field(None, description="深度睡眠比例（%）", ge=0, le=100)
    fatigue_score: Optional[int] = Field(None, description="疲劳感评分（1-5）", ge=1, le=5)
    recovery_activities: Optional[List[str]] = Field(None, description="恢复性活动记录，如拉伸、瑜伽等")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="运动表现指标，如最大力量、耐力、跑步速度等")
    exercise_history: Optional[List[Dict]] = Field(None, description="运动历史记录")
    training_time_preference: Optional[str] = Field(None, description="训练时间偏好，如早晨、下午、晚上")
    equipment_preferences: Optional[List[str]] = Field(None, description="设备偏好，如哑铃、跑步机、动感单车等")

class UserProfile(BaseModel):
    """用户基本档案模型"""
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    nickname: Optional[str] = Field(None, description="昵称")
    email: EmailStr = Field(..., description="邮箱")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    birth_date: Optional[date] = Field(None, description="出生日期")
    age: Optional[int] = Field(None, description="年龄")
    gender: Optional[str] = Field(
        None, 
        description="性别",
        pattern="^(男|女|其他)$"
    )
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

class CompleteProfile(BaseModel):
    """完整用户档案模型"""
    schema_version: str = "1.0"
    user_profile: UserProfile
    health_profile: HealthProfile
    diet_profile: DietProfile
    fitness_profile: FitnessProfile
    extended_attributes: Optional[Dict] = Field({}, description="扩展属性")

class BasicInfoUpdate(BaseModel):
    """基础信息更新模型"""
    birth_date: Optional[date] = Field(None, description="出生日期")
    gender: Optional[str] = Field(
        None, 
        description="性别",
        pattern="^(男|女|其他)$"
    )
    height: Optional[float] = Field(None, description="身高（厘米）", ge=0, le=300)
    weight: Optional[float] = Field(None, description="体重（千克）", ge=0, le=500)
    body_fat_percentage: Optional[float] = Field(None, description="体脂率（%）", ge=0, le=100)
    muscle_mass: Optional[float] = Field(None, description="肌肉量（千克）", ge=0, le=200)
    health_conditions: Optional[List[str]] = Field(None, description="健康状况")
    extended_attributes: Optional[Dict] = Field(None, description="扩展属性")

class DietPreferencesUpdate(BaseModel):
    """饮食偏好更新模型"""
    cooking_skill_level: Optional[str] = Field(
        None, 
        description="烹饪技能水平",
        pattern="^(初级|中级|高级)$"
    )
    favorite_cuisines: Optional[List[str]] = Field(None, description="喜好的菜系")
    dietary_restrictions: Optional[List[str]] = Field(None, description="饮食限制")
    allergies: Optional[List[str]] = Field(None, description="食物过敏")
    nutrition_goals: Optional[Dict] = Field(None, description="营养目标")
    calorie_preference: Optional[int] = Field(None, description="每日卡路里目标", ge=0)
    extended_attributes: Optional[Dict] = Field(None, description="扩展属性")

class FitnessPreferencesUpdate(BaseModel):
    """健身偏好更新模型"""
    fitness_level: Optional[str] = Field(
        None, 
        description="健身水平",
        pattern="^(初级|中级|高级)$"
    )
    exercise_frequency: Optional[int] = Field(
        None, 
        description="每周运动频率",
        ge=0,
        le=7
    )
    preferred_exercises: Optional[List[str]] = Field(None, description="偏好的运动类型")
    fitness_goals: Optional[List[str]] = Field(None, description="健身目标")
    sleep_duration: Optional[float] = Field(None, description="每晚睡眠时长（小时）", ge=0)
    deep_sleep_percentage: Optional[float] = Field(None, description="深度睡眠比例（%）", ge=0, le=100)
    fatigue_score: Optional[int] = Field(None, description="疲劳感评分（1-5）", ge=1, le=5)
    recovery_activities: Optional[List[str]] = Field(None, description="恢复性活动记录")
    short_term_goals: Optional[List[str]] = Field(None, description="短期健身目标")
    long_term_goals: Optional[List[str]] = Field(None, description="长期健身目标")
    goal_progress: Optional[float] = Field(None, description="目标进度百分比", ge=0, le=100)
    training_type: Optional[str] = Field(None, description="训练类型")
    training_progress: Optional[float] = Field(None, description="训练进度百分比", ge=0, le=100)
    muscle_group_analysis: Optional[Dict[str, Any]] = Field(None, description="肌肉群分析")
    extended_attributes: Optional[Dict] = Field(None, description="扩展属性")

class UpdateResponse(BaseModel):
    """更新响应模型"""
    schema_version: str = "1.0"
    message: str
    updated_fields: Optional[List[str]] = None

class HealthStatsResponse(BaseModel):
    """健康数据统计响应模型"""
    schema_version: str = "1.0"
    period: str
    body_metrics_trend: Dict[str, List[float]]
    nutrition_summary: Dict[str, Any]
    fitness_summary: Dict[str, Any]

class ExerciseSet(BaseModel):
    """运动组数模型"""
    reps: int = Field(..., description="重复次数", ge=0)
    weight: Optional[float] = Field(None, description="重量（千克）", ge=0)
    duration: Optional[int] = Field(None, description="持续时间（秒）", ge=0)
    distance: Optional[float] = Field(None, description="距离（米）", ge=0)

class ExerciseRecord(BaseModel):
    """运动记录模型"""
    id: str = Field(..., description="记录ID")
    user_id: str = Field(..., description="用户ID")
    exercise_name: str = Field(..., description="运动名称")
    exercise_type: str = Field(..., description="运动类型", pattern="^(力量|有氧|拉伸|其他)$")
    sets: List[ExerciseSet] = Field(..., description="运动组数详情")
    calories_burned: Optional[float] = Field(None, description="消耗卡路里", ge=0)
    notes: Optional[str] = Field(None, description="备注")
    recorded_at: datetime = Field(..., description="记录时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

class FoodItem(BaseModel):
    """食物项目模型"""
    food_name: str = Field(..., description="食物名称")
    portion: float = Field(..., description="份量（克）", ge=0)
    calories: float = Field(..., description="卡路里", ge=0)
    protein: Optional[float] = Field(None, description="蛋白质（克）", ge=0)
    carbs: Optional[float] = Field(None, description="碳水化合物（克）", ge=0)
    fat: Optional[float] = Field(None, description="脂肪（克）", ge=0)
    fiber: Optional[float] = Field(None, description="膳食纤维（克）", ge=0)

class MealRecord(BaseModel):
    """餐食记录模型"""
    id: str = Field(..., description="记录ID")
    user_id: str = Field(..., description="用户ID")
    meal_type: str = Field(..., description="餐食类型", pattern="^(早餐|午餐|晚餐|加餐)$")
    food_items: List[FoodItem] = Field(..., description="食物列表")
    total_calories: float = Field(..., description="总卡路里", ge=0)
    location: Optional[str] = Field(None, description="用餐地点")
    mood: Optional[str] = Field(None, description="用餐心情")
    notes: Optional[str] = Field(None, description="备注")
    recorded_at: datetime = Field(..., description="记录时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

class DailyNutritionSummary(BaseModel):
    """每日营养摄入汇总模型"""
    summary_date: date = Field(..., description="日期")  # 重命名字段，避免与日期类型冲突
    user_id: str = Field(..., description="用户ID")
    total_calories: float = Field(0, description="总卡路里")
    total_protein: float = Field(0, description="总蛋白质（克）")
    total_carbs: float = Field(0, description="总碳水化合物（克）")
    total_fat: float = Field(0, description="总脂肪（克）")
    total_fiber: float = Field(0, description="总膳食纤维（克）")
    meals: List[MealRecord] = Field([], description="当日餐食记录")
    exercises: List[ExerciseRecord] = Field([], description="当日运动记录")
    net_calories: float = Field(0, description="净卡路里（摄入-消耗）")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间") 