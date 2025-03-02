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
    FitnessPreferencesUpdate, HealthStatsResponse, UpdateResponse,
    ExerciseRecord, MealRecord, DailyNutritionSummary
)
import logging
import traceback

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
        updated_fields = []
        
        # 更新用户属性
        for field, value in update_data.items():
            if hasattr(current_user, field) and value is not None:
                setattr(current_user, field, value)
                updated_fields.append(field)
        
        # 如果更新了身高和体重，自动计算BMI
        if "height" in updated_fields and "weight" in updated_fields:
            height_m = current_user.height / 100
            current_user.bmi = round(current_user.weight / (height_m * height_m), 1)
            updated_fields.append("bmi")
        
        current_user.updated_at = datetime.now()
        await db.commit()
        
        return UpdateResponse(
            schema_version="1.0",
            message="基础信息更新成功",
            updated_fields=updated_fields
        )
    except Exception as e:
        await db.rollback()
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
        updated_fields = []
        
        # 更新用户属性
        for field, value in update_data.items():
            if hasattr(current_user, field) and value is not None:
                if isinstance(value, list):
                    # 对于列表类型的字段，合并新旧值并去重
                    current_values = set(getattr(current_user, field) or [])
                    new_values = set(value)
                    updated_values = list(current_values | new_values)
                    setattr(current_user, field, updated_values)
                else:
                    setattr(current_user, field, value)
                updated_fields.append(field)
        
        current_user.updated_at = datetime.now()
        await db.commit()
        
        return UpdateResponse(
            schema_version="1.0",
            message="饮食偏好更新成功",
            updated_fields=updated_fields
        )
    except Exception as e:
        await db.rollback()
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
    """更新用户的健身偏好"""
    try:
        updated_fields = []
        
        # 开始更新属性
        for field, value in data.dict(exclude_unset=True).items():
            if hasattr(current_user, field):
                if field in ["preferred_exercises", "fitness_goals", "recovery_activities", 
                            "short_term_goals", "long_term_goals"] and value:
                    # 如果是列表类型字段，合并值并确保唯一性
                    current_value = getattr(current_user, field) or []
                    combined_value = list(set(current_value + value))
                    setattr(current_user, field, combined_value)
                elif field in ["muscle_group_analysis", "extended_attributes"] and value:
                    # 如果是字典类型字段，更新而不是覆盖
                    current_value = getattr(current_user, field) or {}
                    current_value.update(value)
                    setattr(current_user, field, current_value)
                else:
                    setattr(current_user, field, value)
                updated_fields.append(field)
            else:
                # 扩展属性字段处理
                try:
                    if not current_user.extended_attributes:
                        current_user.extended_attributes = {}
                    
                    # 将未识别的字段添加到extended_attributes中
                    current_user.extended_attributes[field] = value
                    updated_fields.append(f"extended_attributes.{field}")
                except Exception as e:
                    logging.warning(f"无法将字段 {field} 添加到extended_attributes: {str(e)}")
        
        # 对于恢复数据的特殊处理
        if hasattr(data, "sleep_duration") and data.sleep_duration is not None:
            current_user.sleep_data = current_user.sleep_data or {}
            current_user.sleep_data["duration"] = data.sleep_duration
            updated_fields.append("sleep_data.duration")
            
        if hasattr(data, "deep_sleep_percentage") and data.deep_sleep_percentage is not None:
            current_user.sleep_data = current_user.sleep_data or {}
            current_user.sleep_data["deep_sleep_percentage"] = data.deep_sleep_percentage
            updated_fields.append("sleep_data.deep_sleep_percentage")
            
        if hasattr(data, "fatigue_score") and data.fatigue_score is not None:
            current_user.recovery_data = current_user.recovery_data or {}
            current_user.recovery_data["fatigue_score"] = data.fatigue_score
            updated_fields.append("recovery_data.fatigue_score")
            
        # 保存更改
        current_user.updated_at = datetime.now()
        await db.commit()
        
        return UpdateResponse(
            schema_version="1.0",
            message="更新用户健身偏好成功",
            updated_fields=updated_fields
        )
    except Exception as e:
        await db.rollback()
        logging.error(f"更新用户健身偏好时出错: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"更新用户健身偏好失败: {str(e)}")

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

@router.post("/exercise", response_model=ExerciseRecord)
async def record_exercise(
    data: ExerciseRecord,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """记录用户的运动数据
    
    Args:
        data: 运动记录数据
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        ExerciseRecord: 创建的运动记录
    """
    try:
        exercise_record = ExerciseRecord(
            user_id=current_user.id,
            exercise_name=data.exercise_name,
            exercise_type=data.exercise_type,
            calories_burned=data.calories_burned,
            notes=data.notes,
            recorded_at=data.recorded_at or datetime.now(),
            sets=[ExerciseSet(**set_data.dict()) for set_data in data.sets]
        )
        
        db.add(exercise_record)
        await db.commit()
        await db.refresh(exercise_record)
        
        return exercise_record
    except Exception as e:
        await db.rollback()
        logging.error(f"记录运动数据失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"记录运动数据失败: {str(e)}"
        )

@router.post("/meal", response_model=MealRecord)
async def record_meal(
    data: MealRecord,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """记录用户的餐食数据
    
    Args:
        data: 餐食记录数据
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        MealRecord: 创建的餐食记录
    """
    try:
        meal_record = MealRecord(
            user_id=current_user.id,
            meal_type=data.meal_type,
            total_calories=data.total_calories,
            location=data.location,
            mood=data.mood,
            notes=data.notes,
            recorded_at=data.recorded_at or datetime.now(),
            food_items=[FoodItem(**item.dict()) for item in data.food_items]
        )
        
        db.add(meal_record)
        await db.commit()
        await db.refresh(meal_record)
        
        # 更新每日营养摄入汇总
        date = meal_record.recorded_at.date()
        summary = await db.execute(
            select(DailyNutritionSummary)
            .where(
                DailyNutritionSummary.user_id == current_user.id,
                DailyNutritionSummary.date == date
            )
        )
        summary = summary.scalar_one_or_none()
        
        if not summary:
            summary = DailyNutritionSummary(
                user_id=current_user.id,
                date=date
            )
            db.add(summary)
        
        # 更新汇总数据
        summary.total_calories += meal_record.total_calories
        summary.total_protein += sum(item.protein or 0 for item in meal_record.food_items)
        summary.total_carbs += sum(item.carbs or 0 for item in meal_record.food_items)
        summary.total_fat += sum(item.fat or 0 for item in meal_record.food_items)
        summary.total_fiber += sum(item.fiber or 0 for item in meal_record.food_items)
        summary.net_calories = summary.total_calories  # 需要减去运动消耗
        
        await db.commit()
        await db.refresh(summary)
        
        return meal_record
    except Exception as e:
        await db.rollback()
        logging.error(f"记录餐食数据失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"记录餐食数据失败: {str(e)}"
        )

@router.get("/nutrition/summary/{date}", response_model=DailyNutritionSummary)
async def get_daily_nutrition_summary(
    date: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定日期的营养摄入汇总
    
    Args:
        date: 日期字符串 (YYYY-MM-DD)
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        DailyNutritionSummary: 每日营养摄入汇总
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        summary = await db.execute(
            select(DailyNutritionSummary)
            .where(
                DailyNutritionSummary.user_id == current_user.id,
                DailyNutritionSummary.date == target_date
            )
        )
        summary = summary.scalar_one_or_none()
        
        if not summary:
            raise HTTPException(
                status_code=404,
                detail=f"未找到{date}的营养摄入汇总数据"
            )
        
        return summary
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式错误，请使用YYYY-MM-DD格式"
        )
    except Exception as e:
        logging.error(f"获取营养摄入汇总失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取营养摄入汇总失败: {str(e)}"
        ) 