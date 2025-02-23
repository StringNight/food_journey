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


async def process_stream_response(
    user_id: str,
    db: AsyncSession,
    messages: List[Dict[str, str]],
    user_message: ChatMessage,
):
    """处理流式响应的通用函数"""
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

    # 尝试从AI回复中提取用户画像更新信息
    updates = ai_client.extract_profile_updates(content)
    if updates:
        await ai_client.process_profile_updates(user_id=user_id, updates=updates, db=db)

    await db.commit()

    # 获取用于响应的历史消息并正确格式化为JSON字符串
    history = await get_chat_history_for_response(user_id, db)
    history_data = {"type": "history", "data": history}
    yield f"data: {json.dumps(history_data)}\n\n"


@router.post("/stream")
async def text_chat_stream(
    text_request: TextRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """处理文本流式聊天请求"""
    try:
        # 验证消息内容
        if not isinstance(text_request.message, str):
            raise HTTPException(status_code=400, detail="消息必须是字符串类型")

        message = text_request.message.strip()
        if not message:
            raise HTTPException(status_code=400, detail="消息不能为空")

        if len(message) > MAX_MESSAGE_LENGTH:
            raise HTTPException(
                status_code=413, detail=f"消息长度不能超过{MAX_MESSAGE_LENGTH}字符"
            )

        # 获取用户画像和聊天历史
        user_profile = await get_user_profile(current_user.id, db)
        chat_history = await get_recent_chat_history(current_user.id, db, limit=5)

        # 保存用户消息
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            type=MessageType.text,
            content=message,
            is_user=True,
            created_at=datetime.now(),
        )
        db.add(user_message)
        await db.commit()

        # 构建消息列表
        messages = ai_client._build_chat_messages(
            user_profile=user_profile,
            current_message=message,
            chat_history=chat_history,
        )

        return StreamingResponse(
            process_stream_response(
                user_id=current_user.id,
                db=db,
                messages=messages,
                user_message=user_message,
            ),
            media_type="text/event-stream",
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"流式文本处理失败: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"流式文本处理失败: {str(e)}")


@router.post("/voice_transcribe")
async def voice_transcribe(
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
    """处理语音流式聊天请求"""
    try:
        # 验证文件类型和大小
        content_type = file.content_type.lower()
        if content_type not in ALLOWED_AUDIO_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的音频格式: {content_type}。支持的格式: {', '.join(ALLOWED_AUDIO_TYPES)}",
            )

        file_size = 0
        file_content = b""
        # MODIFIED
        # async for chunk in file.stream():
        #     file_content += chunk
        #     file_size += len(chunk)
        #     if file_size > MAX_FILE_SIZE:
        #         raise HTTPException(
        #             status_code=413,
        #             detail=f"文件大小超过限制: {MAX_FILE_SIZE} bytes"
        #         )
        file_content = await file.read()
        file_size = len(file_content)

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

        try:
            with open(voice_path, "wb") as f:
                f.write(file_content)
            logger.info(f"语音文件已保存: {voice_path}")

            # 语音转文字 - 使用语音文件的URL作为输入
            voice_url = f"/uploads/voices/{voice_filename}"
            try:
                transcribed_text = await ai_client.process_voice(voice_url)
                if not transcribed_text:
                    raise ValueError("语音识别结果为空")
                logger.info(f"语音识别成功: {transcribed_text}")

            except ValueError as e:
                logger.error(f"语音识别失败: {str(e)}")
                raise HTTPException(status_code=400, detail=f"语音识别失败: {str(e)}")

            # 获取用户画像和聊天历史
            user_profile = await get_user_profile(current_user.id, db)
            chat_history = await get_recent_chat_history(current_user.id, db, limit=5)

            # 保存用户消息
            user_message = ChatMessage(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                type=MessageType.voice,
                content=transcribed_text,
                voice_url=f"/uploads/voices/{voice_filename}",
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

            return StreamingResponse(
                process_stream_response(
                    user_id=current_user.id,
                    db=db,
                    messages=messages,
                    user_message=user_message,
                ),
                media_type="text/event-stream",
            )

        except Exception as e:
            # 清理语音文件
            try:
                if voice_path.exists():
                    voice_path.unlink()
                    logger.info(f"语音文件已删除: {voice_path}")
            except Exception as cleanup_error:
                logger.warning(f"清理语音文件失败: {cleanup_error}")
            raise e

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
    """处理图片流式聊天请求"""
    try:
        # 验证文件类型和大小
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400, detail=f"不支持的图片格式: {file.content_type}"
            )

        file_size = 0
        file_content = b""
        async for chunk in file.stream():
            file_content += chunk
            file_size += len(chunk)
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413, detail=f"文件大小超过限制: {MAX_FILE_SIZE} bytes"
                )

        # 保存图片文件
        image_filename = f"{uuid.uuid4()}.{file.filename.split('.')[-1]}"
        image_path = IMAGE_DIR / image_filename
        with open(image_path, "wb") as f:
            f.write(file_content)

        # 识别图片内容
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
            image_url=f"/uploads/images/{image_filename}",
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

        return StreamingResponse(
            process_stream_response(
                user_id=current_user.id,
                db=db,
                messages=messages,
                user_message=user_message,
            ),
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
