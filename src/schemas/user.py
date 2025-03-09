from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List
from datetime import datetime, date
import re

class UserBase(BaseModel):
    """用户基础模型
    
    包含用户的基本信息字段
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="用户名，3-50个字符"
    )

class UserCreate(UserBase):
    """用户创建模型
    
    用于用户注册的数据验证
    """
    password: str = Field(
        ...,
        min_length=6,
        description="密码，最少6个字符"
    )
    confirm_password: str = Field(
        ...,
        min_length=6,
        description="确认密码"
    )
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        """验证两次输入的密码是否匹配
        
        Args:
            v: 确认密码值
            values: 已验证的字段值
            
        Returns:
            str: 验证通过的确认密码
            
        Raises:
            ValueError: 当密码不匹配时抛出
        """
        if 'password' in values and v != values['password']:
            raise ValueError('两次输入的密码不匹配')
        return v

class UserLogin(BaseModel):
    """用户登录模型
    
    用于用户登录的数据验证
    """
    username: str = Field(
        ...,
        description="用户名"
    )
    password: str = Field(
        ...,
        description="密码"
    )

class UserResponse(UserBase):
    """用户响应模型
    
    用于返回用户信息的数据格式
    """
    id: str = Field(
        ...,
        description="用户ID"
    )
    is_active: bool = Field(
        ...,
        description="用户状态"
    )
    created_at: datetime = Field(
        ...,
        description="创建时间"
    )
    avatar_url: Optional[str] = Field(
        None,
        description="用户头像URL"
    )
    
    # 配置从ORM模型转换
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    """令牌模型
    
    用于返回认证令牌的数据格式
    """
    access_token: str = Field(
        ...,
        description="访问令牌"
    )
    token_type: str = Field(
        "bearer",
        description="令牌类型"
    )
    refresh_token: Optional[str] = Field(
        None,
        description="刷新令牌"
    )

class TokenData(BaseModel):
    """令牌数据模型
    
    用于存储令牌中的用户信息
    """
    username: Optional[str] = Field(
        None,
        description="用户名"
    )
    exp: Optional[datetime] = Field(
        None,
        description="过期时间"
    )

class HealthInfo(BaseModel):
    """用户健康信息模型"""
    height: float = Field(..., description="身高(cm)")
    weight: float = Field(..., description="体重(kg)")
    birth_date: date = Field(..., description="出生日期")
    body_fat_percentage: Optional[float] = Field(None, description="体脂率(%)")
    muscle_mass: Optional[float] = Field(None, description="肌肉含量(kg)")
    fitness_level: str = Field(..., description="运动能力水平", example="beginner")
    exercise_frequency: int = Field(..., description="每周运动频率", ge=0, le=7)
    preferred_exercises: List[str] = Field(default=[], description="偏好的运动类型")
    health_conditions: List[str] = Field(default=[], description="健康状况")
    fitness_goals: List[str] = Field(default=[], description="健身目标")

class UserProfile(BaseModel):
    """完整的用户画像模型，包括基本信息、健康信息、饮食偏好、健身信息以及扩展属性等"""
    user_id: str = Field(..., description="用户ID")

    # 基本信息
    birth_date: Optional[date] = Field(None, description="出生日期")
    gender: Optional[str] = Field(None, description="性别")
    nickname: Optional[str] = Field(None, description="用户昵称")
    age: Optional[int] = Field(None, description="年龄")

    # 健康信息
    height: Optional[float] = Field(None, description="身高(cm)")
    weight: Optional[float] = Field(None, description="体重(kg)")
    body_fat_percentage: Optional[float] = Field(None, description="体脂率(%)")
    muscle_mass: Optional[float] = Field(None, description="肌肉含量(kg)")
    bmr: Optional[int] = Field(None, description="基础代谢率(卡路里)")
    tdee: Optional[int] = Field(None, description="每日总能量消耗(卡路里)")
    bmi: Optional[float] = Field(None, description="体重指数")
    water_ratio: Optional[float] = Field(None, description="身体水分比例(%)")
    health_conditions: Optional[List[str]] = Field(default=[], description="健康状况")
    health_goals: Optional[List[str]] = Field(default=[], description="健康目标")

    # 饮食偏好
    cooking_skill_level: Optional[str] = Field(None, description="烹饪技能水平")
    favorite_cuisines: Optional[List[str]] = Field(default=[], description="喜好菜系")
    dietary_restrictions: Optional[List[str]] = Field(default=[], description="饮食限制")
    allergies: Optional[List[str]] = Field(default=[], description="食物过敏")
    calorie_preference: Optional[int] = Field(None, description="卡路里偏好")
    nutrition_goals: Optional[List[str]] = Field(default=[], description="营养目标")
    eating_habits: Optional[str] = Field(None, description="饮食习惯")
    diet_goal: Optional[str] = Field(None, description="饮食目标")

    # 健身信息
    fitness_level: Optional[str] = Field(None, description="健身水平")
    exercise_frequency: Optional[int] = Field(None, description="每周运动频率", ge=0, le=7)
    preferred_exercises: Optional[List[str]] = Field(default=[], description="偏好的运动类型")
    fitness_goals: Optional[List[str]] = Field(default=[], description="健身目标")
    short_term_goals: Optional[List[str]] = Field(default=[], description="短期健身目标")
    long_term_goals: Optional[List[str]] = Field(default=[], description="长期健身目标")
    goal_progress: Optional[float] = Field(None, description="目标进度百分比")
    training_type: Optional[str] = Field(None, description="训练类型")
    training_progress: Optional[float] = Field(None, description="训练进度百分比")
    muscle_group_analysis: Optional[List[str]] = Field(default=[], description="肌肉群分析")
    sleep_duration: Optional[float] = Field(None, description="每晚睡眠时长(小时)")
    deep_sleep_percentage: Optional[float] = Field(None, description="深度睡眠比例(%)")
    fatigue_score: Optional[int] = Field(None, description="疲劳感评分")
    recovery_activities: Optional[List[str]] = Field(default=[], description="恢复性活动")
    performance_metrics: Optional[List[str]] = Field(default=[], description="运动表现指标")
    exercise_history: Optional[List[dict]] = Field(default=[], description="运动历史记录")
    training_time_preference: Optional[str] = Field(None, description="训练时间偏好")
    equipment_preferences: Optional[List[str]] = Field(default=[], description="设备偏好")

    # 扩展属性
    extended_attributes: Optional[dict] = Field(default={}, description="扩展属性")

    # 时间戳
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        orm_mode = True

class UserProfileUpdate(BaseModel):
    """用户画像更新模型，所有字段均可选，用于批量更新用户画像"""
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    nickname: Optional[str] = None
    age: Optional[int] = None

    height: Optional[float] = None
    weight: Optional[float] = None
    body_fat_percentage: Optional[float] = None
    muscle_mass: Optional[float] = None
    bmr: Optional[int] = None
    tdee: Optional[int] = None
    bmi: Optional[float] = None
    water_ratio: Optional[float] = None
    health_conditions: Optional[List[str]] = None
    health_goals: Optional[List[str]] = None

    cooking_skill_level: Optional[str] = None
    favorite_cuisines: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    calorie_preference: Optional[int] = None
    nutrition_goals: Optional[List[str]] = None
    eating_habits: Optional[str] = None
    diet_goal: Optional[str] = None

    fitness_level: Optional[str] = None
    exercise_frequency: Optional[int] = None
    preferred_exercises: Optional[List[str]] = None
    fitness_goals: Optional[List[str]] = None
    short_term_goals: Optional[List[str]] = None
    long_term_goals: Optional[List[str]] = None
    goal_progress: Optional[float] = None
    training_type: Optional[str] = None
    training_progress: Optional[float] = None
    muscle_group_analysis: Optional[List[str]] = None
    sleep_duration: Optional[float] = None
    deep_sleep_percentage: Optional[float] = None
    fatigue_score: Optional[int] = None
    recovery_activities: Optional[List[str]] = None
    performance_metrics: Optional[List[str]] = None
    exercise_history: Optional[List[dict]] = None
    training_time_preference: Optional[str] = None
    equipment_preferences: Optional[List[str]] = None

    extended_attributes: Optional[dict] = None