from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timezone
from ..models.workout import ExerciseType
from pydantic import validator

class WorkoutExerciseBase(BaseModel):
    """训练项目基础模型"""
    exercise_type: str = Field(
        ...,
        description="运动类型",
        pattern="^(STRENGTH|CARDIO|FLEXIBILITY)$"
    )
    exercise_name: str = Field(
        ...,
        description="运动项目名称",
        min_length=1,
        max_length=50
    )
    sets: Optional[int] = Field(
        None,
        description="组数",
        ge=1,
        le=100
    )
    reps: Optional[int] = Field(
        None,
        description="每组重复次数",
        ge=1,
        le=1000
    )
    weight: Optional[float] = Field(
        None,
        description="重量(千克)",
        ge=0,
        le=1000
    )
    distance: Optional[float] = Field(
        None,
        description="距离(公里)",
        ge=0,
        le=1000
    )
    speed: Optional[float] = Field(
        None,
        description="速度(公里/小时)",
        ge=0,
        le=100
    )
    duration: Optional[int] = Field(
        None,
        description="该项目持续时间(分钟)",
        ge=0,
        le=1440  # 24小时
    )
    calories: Optional[int] = Field(
        None,
        description="消耗卡路里",
        ge=0,
        le=10000
    )
    notes: Optional[str] = Field(
        None,
        description="该项目备注",
        max_length=500
    )

class WorkoutExerciseCreate(WorkoutExerciseBase):
    """创建训练项目的请求模型"""
    pass

class WorkoutExercise(WorkoutExerciseBase):
    """训练项目的响应模型"""
    id: int = Field(..., description="训练项目ID")
    workout_id: int = Field(..., description="所属训练记录ID")

    class Config:
        from_attributes = True

class WorkoutBase(BaseModel):
    """训练记录基础模型"""
    name: str = Field(
        ...,
        description="训练计划名称",
        min_length=1,
        max_length=100
    )
    notes: Optional[str] = Field(
        None,
        description="训练备注",
        max_length=1000
    )
    duration: Optional[int] = Field(
        None,
        description="训练时长(分钟)",
        ge=0,
        le=1440  # 24小时
    )

class WorkoutCreate(WorkoutBase):
    """创建训练记录的请求模型"""
    workout_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="训练日期",
        json_schema_extra={
            "example": "2024-01-01T00:00:00Z"
        }
    )
    exercises: List[WorkoutExerciseCreate] = Field(..., description="训练项目列表")

    @validator('workout_date')
    def validate_workout_date(cls, v):
        """验证并确保时区信息"""
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        elif v.tzinfo != timezone.utc:
            v = v.astimezone(timezone.utc)
        return v

class WorkoutUpdate(WorkoutBase):
    """更新训练记录的请求模型"""
    workout_date: Optional[datetime] = Field(
        None,
        description="训练日期",
        json_schema_extra={
            "example": "2024-01-01T00:00:00Z"
        }
    )
    exercises: Optional[List[WorkoutExerciseCreate]] = Field(None, description="训练项目列表")

    @validator('workout_date')
    def validate_workout_date(cls, v):
        """验证并确保时区信息"""
        if v is not None:
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            elif v.tzinfo != timezone.utc:
                v = v.astimezone(timezone.utc)
        return v

class Workout(WorkoutBase):
    """训练记录的响应模型"""
    id: int = Field(..., description="训练记录ID")
    user_id: str = Field(..., description="用户ID")
    workout_date: datetime = Field(..., description="训练日期")
    exercises: Optional[List[WorkoutExercise]] = Field(default_factory=list, description="训练项目列表")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class WorkoutTextInput(BaseModel):
    """训练文本输入模型"""
    text: str = Field(..., description="训练描述文本")

class WorkoutResponse(BaseModel):
    """训练记录响应模型"""
    schema_version: str = "1.0"
    workout: Workout

class WorkoutListResponse(BaseModel):
    """训练记录列表响应模型"""
    schema_version: str = "1.0"
    workouts: List[Workout]
    pagination: Dict = Field(..., description="分页信息")

class WorkoutSearchParams(BaseModel):
    """训练记录搜索参数模型"""
    page: int = Field(1, gt=0, description="页码")
    per_page: int = Field(20, gt=0, le=100, description="每页数量")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    exercise_type: Optional[str] = Field(None, description="运动类型过滤", pattern="^(STRENGTH|CARDIO|FLEXIBILITY)$")

class WorkoutStatsParams(BaseModel):
    """训练统计参数模型"""
    start_date: Optional[datetime] = Field(None, description="统计开始日期")
    end_date: Optional[datetime] = Field(None, description="统计结束日期")

class WorkoutStats(BaseModel):
    """训练统计数据模型"""
    total_workouts: int = Field(..., description="训练总次数")
    total_duration: int = Field(..., description="总训练时长(分钟)")
    strength_count: int = Field(..., description="力量训练次数")
    cardio_count: int = Field(..., description="有氧运动次数")
    flexibility_count: int = Field(..., description="柔韧性训练次数")

class WorkoutStatsResponse(BaseModel):
    """训练统计响应模型"""
    schema_version: str = "1.0"
    stats: WorkoutStats 