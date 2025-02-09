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

class UserProfile(BaseModel):
    """用户基本档案模型"""
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    birth_date: Optional[date] = Field(None, description="出生日期")
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