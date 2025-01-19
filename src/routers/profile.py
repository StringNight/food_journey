from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
from ..models.user import User
from ..database import get_db
from ..auth.jwt import get_current_user
from ..schemas.profile import (
    CompleteProfile, BasicInfoUpdate, DietPreferencesUpdate,
    FitnessPreferencesUpdate, HealthStatsResponse, UpdateResponse
)
import logging

router = APIRouter()

@router.get("", response_model=CompleteProfile)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的完整画像信息
    
    Args:
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        CompleteProfile: 包含用户所有档案信息的响应
    """
    try:
        return CompleteProfile(
            schema_version="1.0",
            user_profile={
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "avatar_url": current_user.avatar_url,
                "birth_date": current_user.birth_date,
                "gender": current_user.gender,
                "created_at": current_user.created_at,
                "updated_at": current_user.updated_at
            },
            health_profile={
                "height": current_user.height,
                "weight": current_user.weight,
                "body_fat_percentage": current_user.body_fat_percentage,
                "muscle_mass": current_user.muscle_mass,
                "bmr": current_user.bmr,
                "tdee": current_user.tdee,
                "health_conditions": current_user.health_conditions
            },
            diet_profile={
                "cooking_skill_level": current_user.cooking_skill_level,
                "favorite_cuisines": current_user.favorite_cuisines,
                "dietary_restrictions": current_user.dietary_restrictions,
                "allergies": current_user.allergies,
                "nutrition_goals": current_user.nutrition_goals
            },
            fitness_profile={
                "fitness_level": current_user.fitness_level,
                "exercise_frequency": current_user.exercise_frequency,
                "preferred_exercises": current_user.preferred_exercises,
                "fitness_goals": current_user.fitness_goals
            },
            extended_attributes=current_user.extended_attributes or {}
        )
    except Exception as e:
        logging.error(f"获取用户档案失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取用户档案失败: {str(e)}"
        )

@router.put("/basic", response_model=UpdateResponse)
async def update_basic_info(
    data: BasicInfoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户的基础信息和健康数据
    
    Args:
        data: 基础信息更新数据
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        UpdateResponse: 包含更新结果的响应
    """
    try:
        update_data = data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(current_user, field, value)
        
        current_user.updated_at = datetime.now()
        await db.commit()
        
        return UpdateResponse(
            schema_version="1.0",
            message="基础信息更新成功"
        )
    except Exception as e:
        logging.error(f"更新基础信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"更新基础信息失败: {str(e)}"
        )

@router.put("/diet", response_model=UpdateResponse)
async def update_diet_preferences(
    data: DietPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户的饮食偏好
    
    Args:
        data: 饮食偏好更新数据
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        UpdateResponse: 包含更新结果的响应
    """
    try:
        update_data = data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(current_user, field, value)
        
        current_user.updated_at = datetime.now()
        await db.commit()
        
        return UpdateResponse(
            schema_version="1.0",
            message="饮食偏好更新成功"
        )
    except Exception as e:
        logging.error(f"更新饮食偏好失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"更新饮食偏好失败: {str(e)}"
        )

@router.put("/fitness", response_model=UpdateResponse)
async def update_fitness_preferences(
    data: FitnessPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户的运动偏好
    
    Args:
        data: 运动偏好更新数据
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        UpdateResponse: 包含更新结果的响应
    """
    try:
        update_data = data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(current_user, field, value)
        
        current_user.updated_at = datetime.now()
        await db.commit()
        
        return UpdateResponse(
            schema_version="1.0",
            message="运动偏好更新成功"
        )
    except Exception as e:
        logging.error(f"更新运动偏好失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"更新运动偏好失败: {str(e)}"
        )

@router.get("/stats", response_model=HealthStatsResponse)
async def get_health_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    stat_type: str = "daily",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的综合健康数据统计
    
    Args:
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
        stat_type: 统计类型，默认为daily
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        HealthStatsResponse: 包含健康数据统计的响应
    """
    try:
        # 这里需要实现具体的统计逻辑
        # 可以从各个相关表中查询数据并进行统计
        
        return HealthStatsResponse(
            schema_version="1.0",
            period=f"{start_date}/{end_date}",
            body_metrics_trend={
                "weight": [current_user.weight],  # 示例数据
                "body_fat": [current_user.body_fat_percentage],
                "muscle_mass": [current_user.muscle_mass]
            },
            nutrition_summary={
                "average_daily_calories": 2000,  # 示例数据
                "average_macros": {
                    "protein": 80,
                    "carbs": 250,
                    "fat": 65
                },
                "meal_patterns": {
                    "most_common_breakfast": ["燕麦", "鸡蛋"],
                    "most_common_cuisines": current_user.favorite_cuisines
                }
            },
            fitness_summary={
                "total_workouts": 12,  # 示例数据
                "total_duration": 360,
                "total_calories_burned": 3000,
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
        )
    except Exception as e:
        logging.error(f"获取健康数据统计失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取健康数据统计失败: {str(e)}"
        ) 