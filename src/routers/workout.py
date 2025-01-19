from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, update, and_
from typing import List, Optional
from datetime import datetime, timedelta, date
from collections import defaultdict
from datetime import timezone

from ..database import get_db
from ..models.workout import (
    Workout as WorkoutModel, 
    WorkoutExercise as WorkoutExerciseModel,
    ExerciseType
)
from ..schemas.workout import (
    WorkoutCreate, WorkoutUpdate, Workout, WorkoutExercise, WorkoutTextInput,
    WorkoutResponse, WorkoutListResponse, WorkoutSearchParams, WorkoutStats, WorkoutStatsResponse,
    WorkoutStatsParams
)
from ..auth.jwt import get_current_user
from ..models.user import User
from ..services.ai_service_client import AIServiceClient
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
ai_client = AIServiceClient()

@router.post("", response_model=WorkoutResponse, status_code=201)
async def create_workout(
    workout: WorkoutCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建训练记录
    
    Args:
        workout: 训练记录创建数据
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        WorkoutResponse: 包含创建的训练记录的响应
    
    Raises:
        HTTPException: 当创建失败时抛出的异常
    """
    # 验证训练日期不能是未来日期
    workout_date = workout.workout_date or datetime.now(timezone.utc)
    if workout_date > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="不能创建未来日期的运动记录"
        )

    try:
        # 创建训练记录
        db_workout = WorkoutModel(
            user_id=current_user.id,
            name=workout.name,
            notes=workout.notes,
            duration=workout.duration,
            workout_date=workout_date,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(db_workout)
        await db.flush()  # 获取workout_id
        
        # 创建训练项目记录
        db_exercises = []
        for exercise in workout.exercises:
            db_exercise = WorkoutExerciseModel(
                workout_id=db_workout.id,
                **exercise.model_dump()
            )
            db.add(db_exercise)
            db_exercises.append(db_exercise)
        
        await db.commit()
        
        # 手动构建完整的Workout对象
        response_workout = Workout(
            id=db_workout.id,
            user_id=db_workout.user_id,
            name=db_workout.name,
            notes=db_workout.notes,
            duration=db_workout.duration,
            workout_date=db_workout.workout_date,
            created_at=db_workout.created_at,
            updated_at=db_workout.updated_at,
            exercises=[
                WorkoutExercise(
                    id=ex.id,
                    workout_id=ex.workout_id,
                    exercise_type=ex.exercise_type,
                    exercise_name=ex.exercise_name,
                    sets=ex.sets,
                    reps=ex.reps,
                    weight=ex.weight,
                    distance=ex.distance,
                    speed=ex.speed,
                    duration=ex.duration,
                    calories=ex.calories,
                    notes=ex.notes
                ) for ex in db_exercises
            ]
        )
        
        return WorkoutResponse(
            schema_version="1.0",
            workout=response_workout
        )
    except Exception as e:
        await db.rollback()
        logging.error(f"创建训练记录失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="创建训练记录失败，请稍后重试"
        )

@router.get("", response_model=WorkoutListResponse)
async def list_workouts(
    search_params: WorkoutSearchParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的训练记录列表
    
    Args:
        search_params: 搜索参数
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        WorkoutListResponse: 包含训练记录列表和分页信息的响应
    """
    try:
        query = select(WorkoutModel).filter(WorkoutModel.user_id == current_user.id)
        
        # 应用过滤条件
        if search_params.start_date:
            # 处理开始日期
            start_date = search_params.start_date
            if isinstance(start_date, date):
                # 如果是纯日期，转换为当天开始时间的datetime
                start_date = datetime.combine(start_date, datetime.min.time())
            if start_date.tzinfo is None:
                # 如果没有时区信息，假定为本地时间，转换为UTC
                start_date = start_date.astimezone(timezone.utc)
            elif start_date.tzinfo != timezone.utc:
                start_date = start_date.astimezone(timezone.utc)
            query = query.filter(WorkoutModel.workout_date >= start_date)
            
        if search_params.end_date:
            # 处理结束日期
            end_date = search_params.end_date
            if isinstance(end_date, date):
                # 如果是纯日期，转换为当天结束时间的datetime
                end_date = datetime.combine(end_date, datetime.max.time())
            if end_date.tzinfo is None:
                # 如果没有时区信息，假定为本地时间，转换为UTC
                end_date = end_date.astimezone(timezone.utc)
            elif end_date.tzinfo != timezone.utc:
                end_date = end_date.astimezone(timezone.utc)
            query = query.filter(WorkoutModel.workout_date <= end_date)
            
        if search_params.exercise_type:
            query = query.join(WorkoutExerciseModel).filter(
                WorkoutExerciseModel.exercise_type == search_params.exercise_type
            ).distinct()  # 添加distinct()避免重复
        
        # 计算总数
        count_query = select(func.count(WorkoutModel.id.distinct())).select_from(query.subquery())
        total = await db.scalar(count_query)
        total_pages = (total + search_params.per_page - 1) // search_params.per_page
        
        # 获取分页数据
        result = await db.execute(
            query.distinct()
            .order_by(WorkoutModel.workout_date.desc())
            .offset((search_params.page - 1) * search_params.per_page)
            .limit(search_params.per_page)
        )
        workouts = result.unique().scalars().all()
        
        # 获取每个训练记录的训练项目
        response_workouts = []
        for workout in workouts:
            exercise_result = await db.execute(
                select(WorkoutExerciseModel)
                .filter(WorkoutExerciseModel.workout_id == workout.id)
            )
            exercises = exercise_result.scalars().all()
            
            response_workout = Workout(
                id=workout.id,
                user_id=workout.user_id,
                name=workout.name,
                notes=workout.notes,
                duration=workout.duration,
                workout_date=workout.workout_date,
                created_at=workout.created_at,
                updated_at=workout.updated_at,
                exercises=[
                    WorkoutExercise(
                        id=ex.id,
                        workout_id=ex.workout_id,
                        exercise_type=ex.exercise_type,
                        exercise_name=ex.exercise_name,
                        sets=ex.sets,
                        reps=ex.reps,
                        weight=ex.weight,
                        distance=ex.distance,
                        speed=ex.speed,
                        duration=ex.duration,
                        calories=ex.calories,
                        notes=ex.notes
                    ) for ex in exercises
                ]
            )
            response_workouts.append(response_workout)
        
        return WorkoutListResponse(
            schema_version="1.0",
            workouts=response_workouts,
            pagination={
                "total": total,
                "page": search_params.page,
                "per_page": search_params.per_page,
                "total_pages": total_pages
            }
        )
    except Exception as e:
        logging.error(f"获取训练记录列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取训练记录列表失败，请稍后重试"
        )

@router.get("/stats", response_model=WorkoutStatsResponse)
async def get_workout_stats(
    start_date: Optional[str] = Query(None, description="统计开始日期 (ISO格式: YYYY-MM-DD 或 YYYY-MM-DDTHH:MM:SSZ)"),
    end_date: Optional[str] = Query(None, description="统计结束日期 (ISO格式: YYYY-MM-DD 或 YYYY-MM-DDTHH:MM:SSZ)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取训练统计数据
    
    Args:
        start_date: 统计开始日期
        end_date: 统计结束日期
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        WorkoutStatsResponse: 包含训练统计数据的响应
    """
    try:
        def parse_date(date_str: Optional[str], is_end_date: bool = False) -> Optional[datetime]:
            """解析日期字符串
            
            Args:
                date_str: 日期字符串
                is_end_date: 是否是结束日期
            
            Returns:
                Optional[datetime]: 解析后的日期时间对象
            """
            if not date_str:
                return None
            
            try:
                if "T" in date_str:
                    # 处理ISO格式的日期时间
                    if date_str.endswith('Z'):
                        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    else:
                        dt = datetime.fromisoformat(date_str)
                    # 确保转换为UTC
                    if dt.tzinfo != timezone.utc:
                        dt = dt.astimezone(timezone.utc)
                    return dt
                else:
                    # 处理纯日期格式
                    base_date = datetime.strptime(date_str, '%Y-%m-%d')
                    if is_end_date:
                        # 对于结束日期，使用当天的23:59:59
                        base_date = base_date.replace(
                            hour=23, minute=59, second=59, microsecond=999999
                        )
                    # 添加 UTC 时区信息
                    return base_date.replace(tzinfo=timezone.utc)
            except ValueError:
                return None  # 返回None而不是抛出异常
        
        parsed_start_date = parse_date(start_date, is_end_date=False)
        parsed_end_date = parse_date(end_date, is_end_date=True)
        
        # 构建基础查询
        query = select(WorkoutModel).filter(WorkoutModel.user_id == current_user.id)
        
        # 添加日期过滤
        if parsed_start_date:
            query = query.filter(WorkoutModel.workout_date >= parsed_start_date)
        if parsed_end_date:
            query = query.filter(WorkoutModel.workout_date <= parsed_end_date)
        
        result = await db.execute(query)
        workouts = result.scalars().all()
        
        # 获取所有训练项目
        workout_ids = [w.id for w in workouts]
        if workout_ids:
            exercise_result = await db.execute(
                select(WorkoutExerciseModel)
                .filter(WorkoutExerciseModel.workout_id.in_(workout_ids))
            )
            exercises = exercise_result.scalars().all()
        else:
            exercises = []
        
        # 计算统计数据
        total_workouts = len(workouts)
        total_duration = sum(w.duration or 0 for w in workouts)
        
        # 统计不同类型的训练次数
        strength_count = sum(1 for ex in exercises if ex.exercise_type == ExerciseType.STRENGTH)
        cardio_count = sum(1 for ex in exercises if ex.exercise_type == ExerciseType.CARDIO)
        flexibility_count = sum(1 for ex in exercises if ex.exercise_type == ExerciseType.FLEXIBILITY)
        
        # 构造统计数据对象
        stats = WorkoutStats(
            total_workouts=total_workouts,
            total_duration=total_duration,
            strength_count=strength_count,
            cardio_count=cardio_count,
            flexibility_count=flexibility_count
        )
        
        # 构造并返回响应
        return WorkoutStatsResponse(
            schema_version="1.0",
            stats=stats
        )
    except Exception as e:
        logger.error(f"获取训练统计数据时发生错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取训练统计数据时发生错误"
        )

@router.get("/{workout_id}", response_model=WorkoutResponse)
async def get_workout(
    workout_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取特定训练记录的详细信息
    
    Args:
        workout_id: 训练记录ID
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        WorkoutResponse: 包含训练记录详细信息的响应
    """
    try:
        result = await db.execute(
            select(WorkoutModel).filter(
                WorkoutModel.id == workout_id,
                WorkoutModel.user_id == current_user.id
            )
        )
        workout = result.scalar_one_or_none()
        
        if not workout:
            raise HTTPException(status_code=404, detail="训练记录不存在")
        
        # 获取训练项目
        exercise_result = await db.execute(
            select(WorkoutExerciseModel)
            .filter(WorkoutExerciseModel.workout_id == workout_id)
        )
        exercises = exercise_result.scalars().all()
        
        response_workout = Workout(
            id=workout.id,
            user_id=workout.user_id,
            name=workout.name,
            notes=workout.notes,
            duration=workout.duration,
            workout_date=workout.workout_date,
            created_at=workout.created_at,
            updated_at=workout.updated_at,
            exercises=[
                WorkoutExercise(
                    id=ex.id,
                    workout_id=ex.workout_id,
                    exercise_type=ex.exercise_type,
                    exercise_name=ex.exercise_name,
                    sets=ex.sets,
                    reps=ex.reps,
                    weight=ex.weight,
                    distance=ex.distance,
                    speed=ex.speed,
                    duration=ex.duration,
                    calories=ex.calories,
                    notes=ex.notes
                ) for ex in exercises
            ]
        )
        
        return WorkoutResponse(
            schema_version="1.0",
            workout=response_workout
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"获取训练记录详情失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取训练记录详情失败: {str(e)}"
        )

@router.put("/{workout_id}", response_model=WorkoutResponse)
async def update_workout(
    workout_id: int,
    workout_update: WorkoutUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新训练记录
    
    Args:
        workout_id: 训练记录ID
        workout_update: 训练记录更新数据
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        WorkoutResponse: 包含更新后的训练记录的响应
    """
    try:
        # 首先获取当前记录
        result = await db.execute(
            select(WorkoutModel).filter(
                WorkoutModel.id == workout_id,
                WorkoutModel.user_id == current_user.id
            )
        )
        workout = result.scalar_one_or_none()
        
        if not workout:
            raise HTTPException(
                status_code=404,
                detail="训练记录不存在"
            )
            
        # 记录更新前的时间戳
        original_updated_at = workout.updated_at
        
        # 准备更新数据
        update_data = {}
        if workout_update.name is not None:
            update_data["name"] = workout_update.name
        if workout_update.notes is not None:
            update_data["notes"] = workout_update.notes
        if workout_update.duration is not None:
            update_data["duration"] = workout_update.duration
        if workout_update.workout_date is not None:
            update_data["workout_date"] = workout_update.workout_date
            
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        # 使用条件更新，只有当updated_at没有变化时才更新
        result = await db.execute(
            update(WorkoutModel)
            .where(
                and_(
                    WorkoutModel.id == workout_id,
                    WorkoutModel.user_id == current_user.id,
                    WorkoutModel.updated_at == original_updated_at
                )
            )
            .values(**update_data)
        )
        
        if result.rowcount == 0:
            # 如果没有更新任何行，说明发生了并发更新
            raise HTTPException(
                status_code=409,
                detail="记录已被其他请求更新，请重试"
            )
            
        # 如果提供了新的训练项目列表，则更新
        if workout_update.exercises is not None:
            # 删除旧的训练项目
            await db.execute(
                delete(WorkoutExerciseModel).where(
                    WorkoutExerciseModel.workout_id == workout_id
                )
            )
            
            # 创建新的训练项目
            db_exercises = []
            for exercise in workout_update.exercises:
                db_exercise = WorkoutExerciseModel(
                    workout_id=workout_id,
                    **exercise.model_dump()
                )
                db.add(db_exercise)
                db_exercises.append(db_exercise)
        else:
            # 如果没有提供新的训练项目列表，则获取现有的训练项目
            exercise_result = await db.execute(
                select(WorkoutExerciseModel)
                .filter(WorkoutExerciseModel.workout_id == workout_id)
            )
            db_exercises = exercise_result.scalars().all()
        
        # 提交更改
        await db.commit()
        
        # 获取更新后的记录
        result = await db.execute(
            select(WorkoutModel).filter(
                WorkoutModel.id == workout_id
            )
        )
        updated_workout = result.scalar_one()
        
        # 构建响应
        response_workout = Workout(
            id=updated_workout.id,
            user_id=updated_workout.user_id,
            name=updated_workout.name,
            notes=updated_workout.notes,
            duration=updated_workout.duration,
            workout_date=updated_workout.workout_date,
            created_at=updated_workout.created_at,
            updated_at=updated_workout.updated_at,
            exercises=[
                WorkoutExercise(
                    id=ex.id,
                    workout_id=ex.workout_id,
                    exercise_type=ex.exercise_type,
                    exercise_name=ex.exercise_name,
                    sets=ex.sets,
                    reps=ex.reps,
                    weight=ex.weight,
                    distance=ex.distance,
                    speed=ex.speed,
                    duration=ex.duration,
                    calories=ex.calories,
                    notes=ex.notes
                ) for ex in db_exercises
            ]
        )
        
        return WorkoutResponse(
            schema_version="1.0",
            workout=response_workout
        )
            
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logging.error(f"更新训练记录失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="更新训练记录失败，请稍后重试"
        )

@router.delete("/{workout_id}", status_code=204)
async def delete_workout(
    workout_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除训练记录
    
    Args:
        workout_id: 训练记录ID
        current_user: 当前用户
        db: 数据库会话
    """
    try:
        result = await db.execute(
            select(WorkoutModel).filter(
                WorkoutModel.id == workout_id,
                WorkoutModel.user_id == current_user.id
            )
        )
        workout = result.scalar_one_or_none()
        
        if not workout:
            raise HTTPException(status_code=404, detail="训练记录不存在")
        
        # 删除关联的训练项目
        await db.execute(
            delete(WorkoutExerciseModel).filter(
                WorkoutExerciseModel.workout_id == workout_id
            )
        )
        
        # 删除训练记录
        await db.delete(workout)
        await db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logging.error(f"删除训练记录失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"删除训练记录失败: {str(e)}"
        )

@router.post("/text", response_model=WorkoutResponse)
async def create_workout_from_text(
    workout_text: WorkoutTextInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """从文本创建训练记录
    
    Args:
        workout_text: 训练文本输入
        current_user: 当前用户
        db: 数据库会话
    
    Returns:
        WorkoutResponse: 包含创建的训练记录的响应
    """
    try:
        # 使用AI服务处理文本
        workout_data = await ai_client.process_workout_text(workout_text.text)
        
        # 创建训练记录
        db_workout = WorkoutModel(
            user_id=current_user.id,
            name=workout_data.get("name", "训练记录"),
            notes=workout_data.get("notes", ""),
            duration=workout_data.get("duration", 0),
            workout_date=workout_data.get("workout_date", datetime.now(timezone.utc))
        )
        db.add(db_workout)
        await db.flush()  # 获取workout_id
        
        # 创建训练项目记录
        db_exercises = []
        for exercise in workout_data.get("exercises", []):
            db_exercise = WorkoutExerciseModel(
                workout_id=db_workout.id,
                **exercise.model_dump()
            )
            db.add(db_exercise)
            db_exercises.append(db_exercise)
        
        await db.commit()
        
        # 手动构建完整的Workout对象
        response_workout = Workout(
            id=db_workout.id,
            user_id=db_workout.user_id,
            name=db_workout.name,
            notes=db_workout.notes,
            duration=db_workout.duration,
            workout_date=db_workout.workout_date,
            created_at=db_workout.created_at,
            updated_at=db_workout.updated_at,
            exercises=[
                WorkoutExercise(
                    id=ex.id,
                    workout_id=ex.workout_id,
                    exercise_type=ex.exercise_type,
                    exercise_name=ex.exercise_name,
                    sets=ex.sets,
                    reps=ex.reps,
                    weight=ex.weight,
                    distance=ex.distance,
                    speed=ex.speed,
                    duration=ex.duration,
                    calories=ex.calories,
                    notes=ex.notes
                ) for ex in db_exercises
            ]
        )
        
        return WorkoutResponse(
            schema_version="1.0",
            workout=response_workout
        )
    except Exception as e:
        logging.error(f"从文本创建训练记录失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"从文本创建训练记录失败: {str(e)}"
        )