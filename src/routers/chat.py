from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Query,
    Request,
    status,
    Form,
)
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import logging
from pathlib import Path
import base64
from ..database import get_db
from ..auth.jwt import get_current_user
from ..models.user import User, UserProfileModel
from ..models.chat import ChatMessageModel as ChatMessage, MessageType
from ..schemas.chat import (
    TextRequest,
    VoiceRequest,
    ImageRequest,
    MessageResponse,
    MessageHistory,
    PaginationInfo,
)
from ..services.ai_service_client import AIServiceClient
import uuid
import re
from ..services.file import file_service
from fastapi.security import OAuth2PasswordRequestForm
from ..config.limiter import limiter
import json

router = APIRouter()
logger = logging.getLogger(__name__)
ai_client = AIServiceClient()

# 常量定义
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_AUDIO_TYPES = {
    "audio/wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/m4a",
    "audio/x-m4a",
    "audio/aac",
    "audio/ogg",
}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif"}
MAX_MESSAGE_LENGTH = 1000  # 设置最大消息长度为1000字符

# 创建上传目录
UPLOAD_DIR = Path("uploads")
VOICE_DIR = UPLOAD_DIR / "voices"
IMAGE_DIR = UPLOAD_DIR / "images"
VOICE_DIR.mkdir(parents=True, exist_ok=True)
IMAGE_DIR.mkdir(parents=True, exist_ok=True)


async def get_chat_history_for_response(
    user_id: str, db: AsyncSession, limit: int = 10
) -> List[Dict[str, Any]]:
    """获取用于响应的聊天历史"""
    query = (
        select(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    messages = result.scalars().all()

    history = []
    for msg in reversed(messages):
        history.append(
            {
                "content": msg.content,
                "is_user": msg.is_user,
                "created_at": msg.created_at.isoformat(),
                "voice_url": msg.voice_url,
                "image_url": msg.image_url,
                "transcribed_text": msg.transcribed_text,
            }
        )
    return history


async def get_user_profile(user_id: str, db: AsyncSession) -> Dict[str, Any]:
    """获取用户画像信息"""
    query = select(UserProfileModel).filter(UserProfileModel.user_id == user_id)
    result = await db.execute(query)
    profile = result.scalar_one_or_none()

    if not profile:
        return {}

    # 返回完整的用户画像数据，包括基本信息、健康信息、饮食偏好、健身信息及扩展属性
    return {
        "user_id": profile.user_id,
        "birth_date": profile.birth_date.isoformat() if profile.birth_date else None,
        "gender": profile.gender,
        "nickname": profile.nickname,
        "age": ((datetime.now().date() - profile.birth_date).days // 365) if profile.birth_date else None,
        "height": profile.height,
        "weight": profile.weight,
        "body_fat_percentage": profile.body_fat_percentage,
        "muscle_mass": profile.muscle_mass,
        "bmr": profile.bmr,
        "tdee": profile.tdee,
        "bmi": (round(profile.weight / ((profile.height / 100) ** 2), 1) if profile.height and profile.weight else None),
        "water_ratio": profile.water_ratio,
        "health_conditions": profile.health_conditions or [],
        "health_goals": profile.health_goals or [],
        "cooking_skill_level": profile.cooking_skill_level or "",
        "favorite_cuisines": profile.favorite_cuisines or [],
        "dietary_restrictions": profile.dietary_restrictions or [],
        "allergies": profile.allergies or [],
        "calorie_preference": profile.calorie_preference,
        "nutrition_goals": profile.nutrition_goals or [],
        "eating_habits": profile.eating_habits,
        "diet_goal": profile.diet_goal,
        "fitness_level": profile.fitness_level,
        "exercise_frequency": profile.exercise_frequency,
        "preferred_exercises": profile.preferred_exercises or [],
        "fitness_goals": profile.fitness_goals or [],
        "short_term_goals": profile.short_term_goals or [],
        "long_term_goals": profile.long_term_goals or [],
        "goal_progress": profile.goal_progress,
        "training_type": profile.training_type,
        "training_progress": profile.training_progress,
        "muscle_group_analysis": profile.muscle_group_analysis or [],
        "sleep_duration": profile.sleep_duration,
        "deep_sleep_percentage": profile.deep_sleep_percentage,
        "fatigue_score": profile.fatigue_score,
        "recovery_activities": profile.recovery_activities or [],
        "performance_metrics": profile.performance_metrics or [],
        "exercise_history": profile.exercise_history or [],
        "training_time_preference": profile.training_time_preference,
        "equipment_preferences": profile.equipment_preferences or [],
        "extended_attributes": profile.extended_attributes or {}
    }


async def get_recent_chat_history(
    user_id: str, db: AsyncSession, limit: int = 5
) -> List[Dict[str, str]]:
    """获取最近的聊天历史"""
    query = (
        select(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    messages = result.scalars().all()

    history = []
    for msg in reversed(messages):
        history.append(
            {"role": "user" if msg.is_user else "assistant", "content": msg.content}
        )
    return history


# 修改这个函数，整合新旧功能
async def process_stream_response(
    user_id: str,
    db: AsyncSession,
    messages: List[Dict[str, str]],
    user_message: ChatMessage,
):
    """处理流式响应的通用函数"""
    # 使用列表收集响应内容
    full_content = []
    async for chunk in ai_client.chat_stream(messages=messages):
        full_content.append(chunk)
        # 将文本块包装成JSON格式
        chunk_data = {"type": "message", "data": chunk}
        yield f"data: {json.dumps(chunk_data)}\n\n"

    # 保存完整的系统响应
    content = "".join(full_content)
    system_message = ChatMessage(
        id=str(uuid.uuid4()),
        user_id=user_id,
        type=MessageType.text,
        content=content,
        is_user=False,
        created_at=datetime.now(),
    )
    db.add(system_message)
    # 只使用flush，不要在这里commit
    await db.flush()  

    # 用于跟踪是否需要前端刷新数据
    profile_updated = False

    # 在process_stream_response函数中修改用户画像更新部分
    try:
    # 尝试从AI回复中提取用户画像更新信息
        logger.info(f"正在从AI回复中提取用户画像更新信息，用户ID: {user_id}")
        updates = ai_client.extract_profile_updates(content)
        
        if updates:
            logger.info(f"检测到用户画像更新，用户ID: {user_id}, 更新内容: {updates}")
            
            # 记录当前事务状态
            logger.info(f"提取到的用户画像更新，准备处理，事务状态：{db.is_active}")
            
            # 使用独立的数据库会话处理用户画像更新，避免影响主事务
            async with AsyncSession(db.bind) as update_db:
                try:
                    # 开始一个新事务
                    await update_db.begin()
                    
                    # 处理用户画像更新
                    update_result = await ai_client.process_profile_updates(
                        user_id=user_id, 
                        updates=updates, 
                        db=update_db
                    )
                    
                    if update_result["success"] and update_result["updated_fields"]:
                        # 立即提交事务，确保数据更新被保存
                        await update_db.commit()
                        logger.info(f"用户画像更新成功并已提交，用户ID: {user_id}, 更新字段: {update_result['updated_fields']}")
                        
                        # 发送通知前端刷新用户画像数据
                        profile_updated = True
                        update_notification = {
                            "type": "profile_updated",
                            "data": {
                                "message": "用户画像已更新",
                                "updated_fields": update_result["updated_fields"]
                            }
                        }
                        yield f"data: {json.dumps(update_notification)}\n\n"
                except Exception as update_error:
                    # 回滚更新事务，但不影响主事务
                    await update_db.rollback()
                    logger.error(f"用户画像更新失败，已回滚更新事务: {str(update_error)}")
    except Exception as e:
        logger.error(f"处理用户画像更新过程中出错: {str(e)}")
        # 打印详细堆栈信息以便调试
        import traceback
        logger.error(f"出错详细信息: {traceback.format_exc()}")
        # 不要让更新错误影响到主流程

        # 获取用于响应的历史消息并正确格式化为JSON字符串
        history = await get_chat_history_for_response(user_id, db)
        history_data = {"type": "history", "data": history}
        yield f"data: {json.dumps(history_data)}\n\n"
        
        # 如果用户画像已更新，发送一个通知让前端刷新数据
        if profile_updated:
            refresh_data = {
                "type": "profile_updated", 
                "data": {
                    "message": "用户画像已更新，请刷新健身数据",
                    "timestamp": datetime.now().isoformat()
                }
            }
            logger.info(f"发送用户画像更新通知到前端，用户ID: {user_id}")
            yield f"data: {json.dumps(refresh_data)}\n\n"

@router.post("/stream")
async def stream_chat(
    request: TextRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """处理流式聊天请求"""
    try:
        # 生成消息ID
        message_id = str(uuid.uuid4())
        
        # 保存用户消息 - 修改这里，使用固定的 "text" 类型而不是 request.type
        user_message = ChatMessage(
            id=message_id,
            user_id=current_user.id,
            content=request.message,
            type=MessageType.text,  # 使用固定的文本类型
            is_user=True,
            created_at=datetime.now()
        )
        
        # 添加到数据库
        db.add(user_message)
        
        # 获取用户画像和聊天历史
        user_profile = await get_user_profile(current_user.id, db)
        chat_history = await get_recent_chat_history(current_user.id, db, limit=5)
        
        # 立即提交用户消息，释放锁
        await db.commit()
        logger.info(f"用户消息已保存并提交，用户ID: {current_user.id}, 消息ID: {message_id}")
        
        # 构建消息列表
        messages = ai_client._build_chat_messages(
            user_profile=user_profile,
            current_message=request.message,
            chat_history=chat_history,
        )
        
        # 创建流式响应
        response_stream = process_stream_response(
            user_id=current_user.id,
            db=db,
            messages=messages,
            user_message=user_message,
        )
        
        # 注册一个回调，确保流式响应完成后提交数据库事务
        async def stream_with_commit():
            try:
                logger.info(f"开始流式响应处理，用户ID: {current_user.id}")
                async for chunk in response_stream:
                    yield chunk
                # 在提交事务前先执行flush确保所有操作可见
                logger.info(f"流式响应完成，准备提交数据库事务，用户ID: {current_user.id}")
                await db.flush()
                await db.commit()
                logger.info(f"流式响应完成，数据库事务已提交，用户ID: {current_user.id}")
            except Exception as e:
                # 异常情况下回滚事务
                logger.error(f"流式响应出错，回滚数据库事务: {str(e)}, 用户ID: {current_user.id}")
                try:
                    await db.rollback()
                    logger.info(f"已回滚事务，用户ID: {current_user.id}")
                except Exception as rollback_error:
                    logger.error(f"回滚事务失败: {rollback_error}")
                raise
        
        return StreamingResponse(
            stream_with_commit(),
            media_type="text/event-stream",
        )
        
    except Exception as e:
        logger.error(f"流式文本处理失败: {e}")
        # 确保回滚事务
        try:
            await db.rollback()
            logger.info(f"已回滚事务，用户ID: {current_user.id}")
        except Exception as rollback_error:
            logger.error(f"回滚事务失败: {rollback_error}")
        raise HTTPException(status_code=500, detail=f"处理请求失败: {str(e)}")


@router.post("/text_transcribe")
async def text_transcribe(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """语音转写接口
    
    将上传的语音文件转写为文本。支持 wav, mp3, m4a, aac, ogg 格式。
    """
    try:
        # 验证文件类型和大小
        content_type = file.content_type.lower()
        if content_type not in ALLOWED_AUDIO_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的音频格式: {content_type}。支持的格式: {', '.join(ALLOWED_AUDIO_TYPES)}"
            )

        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"文件大小超过限制: {MAX_FILE_SIZE/1024/1024}MB"
            )

        # 调用语音识别服务
        try:
            transcribed_text = await ai_client.process_voice(file_content)
            if not transcribed_text:
                raise ValueError("语音识别结果为空")
                
            return {
                "success": True,
                "text": transcribed_text
            }
            
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"语音识别失败: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"语音转写失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"语音转写失败: {str(e)}"
        )

@router.post("/voice")
async def voice_chat_stream(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """处理语音流式聊天请求，直接返回流式响应"""
    try:
        # 验证文件类型和大小
        content_type = file.content_type.lower()
        if content_type not in ALLOWED_AUDIO_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的音频格式: {content_type}。支持的格式: {', '.join(ALLOWED_AUDIO_TYPES)}",
            )

        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"文件大小超过限制: {MAX_FILE_SIZE} bytes"
            )

        # 保存语音文件, 根据文件类型选择正确的扩展名
        if content_type == "audio/wav":
            ext = "wav"
        elif content_type in {"audio/mpeg", "audio/mp3"}:
            ext = "mp3"
        elif content_type in {"audio/m4a", "audio/x-m4a"}:
            ext = "m4a"
        elif content_type == "audio/aac":
            ext = "aac"
        elif content_type == "audio/ogg":
            ext = "ogg"
        else:
            raise HTTPException(
                status_code=400, detail=f"不支持的音频格式: {content_type}"
            )

        voice_filename = f"{uuid.uuid4()}.{ext}"
        voice_path = VOICE_DIR / voice_filename
        voice_url = f"/uploads/voices/{voice_filename}"

        # 保存文件
        with open(voice_path, "wb") as f:
            f.write(file_content)
        logger.info(f"语音文件已保存: {voice_path}")

        # 语音转文字
        try:
            transcribed_text = await ai_client.process_voice(voice_url)
            if not transcribed_text:
                raise ValueError("语音识别结果为空")
            logger.info(f"语音识别成功: {transcribed_text}")
        except ValueError as e:
            logger.error(f"语音识别失败: {str(e)}")
            transcribed_text = "无法识别语音内容"

        # 获取用户画像和聊天历史
        user_profile = await get_user_profile(current_user.id, db)
        chat_history = await get_recent_chat_history(current_user.id, db, limit=5)

        # 保存用户消息
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            type=MessageType.voice,
            content=transcribed_text,
            voice_url=voice_url,
            transcribed_text=transcribed_text,
            is_user=True,
            created_at=datetime.now(),
        )
        db.add(user_message)
        await db.commit()

        # 构建消息列表
        messages = ai_client._build_chat_messages(
            user_profile=user_profile,
            current_message=transcribed_text,
            chat_history=chat_history,
        )

        # 创建流式响应
        response_stream = process_stream_response(
            user_id=current_user.id,
            db=db,
            messages=messages,
            user_message=user_message,
        )
        
        # 注册一个回调，确保流式响应完成后提交数据库事务
        async def stream_with_commit():
            try:
                logger.info(f"开始流式响应处理，用户ID: {current_user.id}")
                async for chunk in response_stream:
                    yield chunk
                # 在提交事务前先执行flush确保所有操作可见
                logger.info(f"流式响应完成，准备提交数据库事务，用户ID: {current_user.id}")
                await db.flush()
                await db.commit()
                logger.info(f"流式响应完成，数据库事务已提交，用户ID: {current_user.id}")
            except Exception as e:
                # 异常情况下回滚事务
                logger.error(f"流式响应出错，回滚数据库事务: {str(e)}, 用户ID: {current_user.id}")
                await db.rollback()
                raise
                
        return StreamingResponse(
            stream_with_commit(),
            media_type="text/event-stream",
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"流式语音处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"流式语音处理失败: {str(e)}")


@router.post("/image/stream")
async def image_chat_stream(
    file: UploadFile = File(...),
    caption: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """处理图片流式聊天请求，直接返回流式响应"""
    try:
        # 验证文件类型和大小
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400, detail=f"不支持的图片格式: {file.content_type}"
            )

        # 读取文件内容 - 修改这里，确保完全读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, detail=f"文件大小超过限制: {MAX_FILE_SIZE} bytes"
            )

        # 保存图片文件
        image_filename = f"{uuid.uuid4()}.{file.filename.split('.')[-1]}"
        image_path = IMAGE_DIR / image_filename
        image_url = f"/uploads/images/{image_filename}"
        
        # 保存文件
        with open(image_path, "wb") as f:
            f.write(file_content)
        logger.info(f"图片文件已保存: {image_path}")

        # 确保文件指针重置，以防后续需要再次读取
        await file.seek(0)

        # 识别图片内容 - 修改为使用文件路径而不是文件对象
        recognition_result = await ai_client.recognize_food(str(image_path))
        if not recognition_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"图片识别失败: {recognition_result.get('message', '未知错误')}",
            )

        # 构建图片描述
        food_items = recognition_result["food_items"]
        food_description = "图片中包含: " + ", ".join(
            [item["name"] for item in food_items]
        )

        # 组合用户输入的文字说明
        full_message = (
            f"{food_description}\n用户说明: {caption}" if caption else food_description
        )

        # 获取用户画像和聊天历史
        user_profile = await get_user_profile(current_user.id, db)
        chat_history = await get_recent_chat_history(current_user.id, db, limit=5)

        # 保存用户消息
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            type=MessageType.image,
            content=full_message,
            image_url=image_url,
            is_user=True,
            created_at=datetime.now(),
        )
        db.add(user_message)
        await db.commit()

        # 构建消息列表
        messages = ai_client._build_chat_messages(
            user_profile=user_profile,
            current_message=full_message,
            chat_history=chat_history,
        )

        # 创建流式响应
        response_stream = process_stream_response(
            user_id=current_user.id,
            db=db,
            messages=messages,
            user_message=user_message,
        )
        
        # 注册一个回调，确保流式响应完成后提交数据库事务
        async def stream_with_commit():
            try:
                logger.info(f"开始流式响应处理，用户ID: {current_user.id}")
                async for chunk in response_stream:
                    yield chunk
                # 在提交事务前先执行flush确保所有操作可见
                logger.info(f"流式响应完成，准备提交数据库事务，用户ID: {current_user.id}")
                await db.flush()
                await db.commit()
                logger.info(f"流式响应完成，数据库事务已提交，用户ID: {current_user.id}")
            except Exception as e:
                # 异常情况下回滚事务
                logger.error(f"流式响应出错，回滚数据库事务: {str(e)}, 用户ID: {current_user.id}")
                await db.rollback()
                raise
                
        return StreamingResponse(
            stream_with_commit(),
            media_type="text/event-stream",
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"流式图片处理失败: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"流式图片处理失败: {str(e)}")


@router.get("/history", response_model=MessageHistory)
async def get_chat_history(
    page: int = Query(1, gt=0),
    per_page: int = Query(20, gt=0, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取聊天历史记录"""
    try:
        # 构建基础查询
        query = select(ChatMessage).filter(ChatMessage.user_id == current_user.id)

        # 添加日期过滤
        if start_date:
            query = query.filter(ChatMessage.created_at >= start_date)
        if end_date:
            query = query.filter(ChatMessage.created_at <= end_date)

        # 获取总记录数
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)

        # 分页
        query = query.order_by(ChatMessage.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        # 执行查询
        result = await db.execute(query)
        messages = result.scalars().all()

        # 构建响应
        return MessageHistory(
            messages=[
                MessageResponse(
                    id=str(msg.id),
                    content=msg.content,
                    is_user=msg.is_user,
                    created_at=msg.created_at,
                    voice_url=msg.voice_url,
                    image_url=msg.image_url,
                    transcribed_text=msg.transcribed_text,
                )
                for msg in messages
            ],
            pagination=PaginationInfo(
                total=total,
                page=page,
                per_page=per_page,
                total_pages=(total + per_page - 1) // per_page,
            ),
        )

    except Exception as e:
        logger.error(f"获取聊天历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取聊天历史失败: {str(e)}")
