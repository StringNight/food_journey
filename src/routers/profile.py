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
import uuid

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
        # 使用显式查询获取用户的profile数据，而不是通过ORM关系
        from ..models.user import UserProfileModel
        
        # 显式查询用户配置文件
        query = select(UserProfileModel).filter(UserProfileModel.user_id == current_user.id)
        result = await db.execute(query)
        user_profile = result.scalar_one_or_none()
        
        # 创建用户档案响应，明确指定各个字段的默认值
        return CompleteProfile(
            schema_version="1.0",
            user_profile={
                "id": current_user.id,
                "username": current_user.username,
                "avatar_url": current_user.avatar_url,
                # 从查询结果中获取这些字段，如果profile不存在则返回None
                "birth_date": user_profile.birth_date if user_profile else None,
                "gender": user_profile.gender if user_profile else None,
                "created_at": current_user.created_at,
                "updated_at": current_user.updated_at
            },
            health_profile={
                "height": user_profile.height if user_profile else None,
                "weight": user_profile.weight if user_profile else None,
                "body_fat_percentage": user_profile.body_fat_percentage if user_profile else None,
                "muscle_mass": user_profile.muscle_mass if user_profile else None,
                "bmr": user_profile.bmr if user_profile else None,
                "tdee": user_profile.tdee if user_profile else None,
                "health_conditions": user_profile.health_conditions if user_profile else None,
                "bmi": user_profile.bmi if user_profile else None,
                "water_ratio": user_profile.water_ratio if user_profile else None
            },
            diet_profile={
                "cooking_skill_level": user_profile.cooking_skill_level if user_profile else None,
                "favorite_cuisines": user_profile.favorite_cuisines if user_profile else None,
                "dietary_restrictions": user_profile.dietary_restrictions if user_profile else None,
                "allergies": user_profile.allergies if user_profile else None,
                "nutrition_goals": user_profile.nutrition_goals if user_profile else None,
                "calorie_preference": user_profile.calorie_preference if user_profile else None,
                "eating_habits": user_profile.eating_habits if user_profile else None,
                "diet_goal": user_profile.diet_goal if user_profile else None
            },
            fitness_profile={
                "fitness_level": user_profile.fitness_level if user_profile else None,
                "exercise_frequency": user_profile.exercise_frequency if user_profile else None,
                "preferred_exercises": user_profile.preferred_exercises if user_profile else None,
                "fitness_goals": user_profile.fitness_goals if user_profile else None,
                "short_term_goals": user_profile.short_term_goals if user_profile else None,
                "long_term_goals": user_profile.long_term_goals if user_profile else None,
                "goal_progress": user_profile.goal_progress if user_profile else None,
                "training_type": user_profile.training_type if user_profile else None,
                "training_progress": user_profile.training_progress if user_profile else None,
                "muscle_group_analysis": user_profile.muscle_group_analysis if user_profile else None,
                "sleep_duration": user_profile.sleep_duration if user_profile else None,
                "deep_sleep_percentage": user_profile.deep_sleep_percentage if user_profile else None,
                "fatigue_score": user_profile.fatigue_score if user_profile else None,
                "recovery_activities": user_profile.recovery_activities if user_profile else None,
                "performance_metrics": user_profile.performance_metrics if user_profile else None,
                "exercise_history": user_profile.exercise_history if user_profile else None
            },
            extended_attributes=user_profile.extended_attributes if user_profile else {}
        )
    except Exception as e:
        logging.error(f"获取用户档案失败: {str(e)}")
        logging.error(traceback.format_exc())
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
    """更新用户的基础信息
    
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
        
        # 使用显式查询获取用户的profile数据
        from ..models.user import UserProfileModel
        import uuid
        
        # 查询用户配置文件
        query = select(UserProfileModel).filter(UserProfileModel.user_id == current_user.id)
        result = await db.execute(query)
        user_profile = result.scalar_one_or_none()
        
        # 如果用户没有profile，创建一个新的
        if not user_profile:
            # 创建一个新的profile实例
            user_profile = UserProfileModel(
                id=str(uuid.uuid4()),
                user_id=current_user.id
            )
            db.add(user_profile)
            updated_fields.append("user_profile_created")
        
        # 更新用户和profile属性
        user_fields = ['username', 'avatar_url']
        profile_fields = [
            'birth_date', 'gender', 'height', 'weight', 'body_fat_percentage', 
            'muscle_mass', 'bmr', 'tdee', 'health_conditions', 'extended_attributes'
        ]
        
        for field, value in update_data.items():
            if value is None:
                continue
                
            if field in user_fields and hasattr(current_user, field):
                setattr(current_user, field, value)
                updated_fields.append(field)
            elif field in profile_fields and hasattr(user_profile, field):
                setattr(user_profile, field, value)
                updated_fields.append(field)
        
        # 如果更新了身高和体重，自动计算BMI
        height_updated = 'height' in update_data
        weight_updated = 'weight' in update_data
        
        if height_updated or weight_updated:
            # 如果只更新了一个，获取另一个的当前值
            height = update_data.get('height', user_profile.height if user_profile else None)
            weight = update_data.get('weight', user_profile.weight if user_profile else None)
            
            # 只有当两个值都不为None时才计算BMI
            if height and weight and height > 0:
                height_m = height / 100  # 将厘米转换为米
                user_profile.bmi = round(weight / (height_m * height_m), 1)
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
        logging.error(traceback.format_exc())
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
        updated_fields = []
        
        # 使用显式查询获取用户的profile数据
        from ..models.user import UserProfileModel
        import uuid
        
        # 查询用户配置文件
        query = select(UserProfileModel).filter(UserProfileModel.user_id == current_user.id)
        result = await db.execute(query)
        user_profile = result.scalar_one_or_none()
        
        # 如果用户没有profile，创建一个新的
        if not user_profile:
            # 创建一个新的profile实例
            user_profile = UserProfileModel(
                id=str(uuid.uuid4()),
                user_id=current_user.id
            )
            db.add(user_profile)
            updated_fields.append("user_profile_created")
        
        # 更新饮食偏好
        for field, value in data.dict(exclude_unset=True).items():
            if hasattr(user_profile, field):
                if field in ["favorite_cuisines", "dietary_restrictions", "allergies"] and value:
                    # 如果是列表类型字段，合并值并确保唯一性
                    current_value = getattr(user_profile, field) or []
                    combined_value = list(set(current_value + value))
                    setattr(user_profile, field, combined_value)
                elif field == "nutrition_goals" and value:
                    # 如果是字典类型字段，更新而不是覆盖
                    current_value = user_profile.nutrition_goals or {}
                    current_value.update(value)
                    user_profile.nutrition_goals = current_value
                else:
                    setattr(user_profile, field, value)
                updated_fields.append(field)
            else:
                # 扩展属性字段处理
                try:
                    if not user_profile.extended_attributes:
                        user_profile.extended_attributes = {}
                    
                    # 将未识别的字段添加到extended_attributes中
                    user_profile.extended_attributes[field] = value
                    updated_fields.append(f"extended_attributes.{field}")
                except Exception as e:
                    logging.warning(f"无法将字段 {field} 添加到extended_attributes: {str(e)}")
        
        await db.commit()
        
        return UpdateResponse(
            schema_version="1.0",
            message="饮食偏好更新成功",
            updated_fields=updated_fields
        )
    except Exception as e:
        await db.rollback()
        logging.error(f"更新饮食偏好失败: {str(e)}")
        logging.error(traceback.format_exc())
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
        
        # 使用显式查询获取用户的profile数据
        from ..models.user import UserProfileModel
        import uuid
        
        # 查询用户配置文件
        query = select(UserProfileModel).filter(UserProfileModel.user_id == current_user.id)
        result = await db.execute(query)
        user_profile = result.scalar_one_or_none()
        
        # 如果用户没有profile，创建一个新的
        if not user_profile:
            # 创建一个新的profile实例
            user_profile = UserProfileModel(
                id=str(uuid.uuid4()),
                user_id=current_user.id
            )
            db.add(user_profile)
            updated_fields.append("user_profile_created")
        
        # 开始更新属性
        for field, value in data.dict(exclude_unset=True).items():
            if hasattr(user_profile, field):
                if field in ["preferred_exercises", "fitness_goals", "recovery_activities", 
                            "short_term_goals", "long_term_goals"] and value:
                    # 如果是列表类型字段，合并值并确保唯一性
                    current_value = getattr(user_profile, field) or []
                    combined_value = list(set(current_value + value))
                    setattr(user_profile, field, combined_value)
                elif field in ["muscle_group_analysis", "extended_attributes"] and value:
                    # 如果是字典类型字段，更新而不是覆盖
                    current_value = getattr(user_profile, field) or {}
                    current_value.update(value)
                    setattr(user_profile, field, current_value)
                else:
                    setattr(user_profile, field, value)
                updated_fields.append(field)
            else:
                # 扩展属性字段处理
                try:
                    if not user_profile.extended_attributes:
                        user_profile.extended_attributes = {}
                    
                    # 将未识别的字段添加到extended_attributes中
                    user_profile.extended_attributes[field] = value
                    updated_fields.append(f"extended_attributes.{field}")
                except Exception as e:
                    logging.warning(f"无法将字段 {field} 添加到extended_attributes: {str(e)}")
        
        await db.commit()
        
        return UpdateResponse(
            schema_version="1.0",
            message="健身偏好更新成功",
            updated_fields=updated_fields
        )
    except Exception as e:
        await db.rollback()
        logging.error(f"更新健身偏好失败: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"更新健身偏好失败: {str(e)}"
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
        # 使用显式查询获取用户的profile数据
        from ..models.user import UserProfileModel
        
        # 查询用户配置文件
        query = select(UserProfileModel).filter(UserProfileModel.user_id == current_user.id)
        result = await db.execute(query)
        user_profile = result.scalar_one_or_none()
        
        # 如果用户没有profile，使用默认值
        weight = user_profile.weight if user_profile and user_profile.weight else 70.0
        body_fat = user_profile.body_fat_percentage if user_profile and user_profile.body_fat_percentage else 20.0
        muscle_mass = user_profile.muscle_mass if user_profile and user_profile.muscle_mass else 35.0
        favorite_cuisines = user_profile.favorite_cuisines if user_profile and user_profile.favorite_cuisines else ["中式", "西式"]
        
        # 这里需要实现具体的统计逻辑
        # 可以从各个相关表中查询数据并进行统计
        
        return HealthStatsResponse(
            schema_version="1.0",
            period=f"{start_date}/{end_date}",
            body_metrics_trend={
                "weight": [weight],  # 示例数据
                "body_fat": [body_fat],
                "muscle_mass": [muscle_mass]
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
                    "most_common_cuisines": favorite_cuisines
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
        logging.error(f"获取健康统计数据失败: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"获取健康统计数据失败: {str(e)}"
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