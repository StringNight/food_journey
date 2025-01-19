from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Request, status
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
from ..models.user import User
from ..models.chat import ChatMessageModel as ChatMessage, MessageType
from ..schemas.chat import (
    TextRequest, VoiceRequest, ImageRequest,
    MessageResponse, MessageHistory, PaginationInfo
)
from ..services.ai_service_client import AIServiceClient
import uuid
import re
from ..services.file import file_service
from fastapi.security import OAuth2PasswordRequestForm
from ..config.limiter import limiter

router = APIRouter()
logger = logging.getLogger(__name__)
ai_client = AIServiceClient()

# 常量定义
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_AUDIO_TYPES = {"audio/wav", "audio/mpeg", "audio/mp3"}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif"}
MAX_MESSAGE_LENGTH = 1000  # 设置最大消息长度为1000字符

# 创建上传目录
UPLOAD_DIR = Path("uploads")
VOICE_DIR = UPLOAD_DIR / "voices"
IMAGE_DIR = UPLOAD_DIR / "images"
VOICE_DIR.mkdir(parents=True, exist_ok=True)
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

async def get_chat_history_for_response(
    user_id: str,
    db: AsyncSession,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """获取用于响应的聊天历史
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        limit: 获取的消息数量
        
    Returns:
        List[Dict[str, Any]]: 聊天历史记录
    """
    # 获取最近的消息
    query = (
        select(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    messages = result.scalars().all()
    
    # 转换为响应格式
    history = []
    for msg in reversed(messages):  # 反转顺序，使其按时间正序
        history.append({
            "content": msg.content,
            "is_user": msg.is_user,
            "created_at": msg.created_at.isoformat(),
            "voice_url": msg.voice_url,
            "image_url": msg.image_url,
            "transcribed_text": msg.transcribed_text
        })
        
    return history

@router.post("/text", response_model=MessageResponse)
async def text_chat(
    text_request: TextRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """处理文本聊天请求"""
    try:
        # 验证消息内容
        if not isinstance(text_request.message, str):
            raise HTTPException(status_code=400, detail="消息必须是字符串类型")
            
        message = text_request.message.strip()
        if not message:
            raise HTTPException(status_code=400, detail="消息不能为空")
            
        if len(message) > MAX_MESSAGE_LENGTH:
            raise HTTPException(
                status_code=413,
                detail=f"消息长度不能超过{MAX_MESSAGE_LENGTH}字符"
            )
            
        # 获取用户画像
        user_profile = await get_user_profile(current_user.id, db)
        
        # 获取最近的聊天历史（最多5条）用于AI上下文
        chat_history = await get_recent_chat_history(current_user.id, db, limit=5)
        
        # 保存用户消息
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            type=MessageType.text,
            content=message,
            is_user=True,
            created_at=datetime.now()
        )
        db.add(user_message)
        
        # 构建完整的消息列表
        messages = ai_client._build_chat_messages(
            user_profile=user_profile,
            current_message=message,
            chat_history=chat_history
        )
        
        # 获取AI响应
        chat_response = await ai_client.chat(
            messages=messages,
            model="qwen2.5:14b"
        )
        
        content = chat_response.get("response", "")
        if not content:
            raise ValueError("AI响应内容为空")
            
        # 保存系统响应
        system_message = ChatMessage(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            type=MessageType.text,
            content=content,
            is_user=False,
            created_at=datetime.now()
        )
        db.add(system_message)
        await db.commit()
        
        # 获取用于响应的历史消息（最多10条）
        history = await get_chat_history_for_response(current_user.id, db)
        
        return MessageResponse(
            schema_version="1.0",
            message=content,
            created_at=system_message.created_at,
            history=history
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"文本处理失败: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"文本处理失败: {str(e)}")

@router.post("/text/stream")
async def text_chat_stream(
    text_request: TextRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """处理流式文本聊天请求"""
    try:
        # 验证消息内容
        if not isinstance(text_request.message, str):
            raise HTTPException(status_code=400, detail="消息必须是字符串类型")
            
        message = text_request.message.strip()
        if not message:
            raise HTTPException(status_code=400, detail="消息不能为空")
            
        if len(message) > MAX_MESSAGE_LENGTH:
            raise HTTPException(
                status_code=413,
                detail=f"消息长度不能超过{MAX_MESSAGE_LENGTH}字符"
            )
            
        # 获取用户画像
        user_profile = await get_user_profile(current_user.id, db)
        
        # 获取最近的聊天历史（最多5条）用于AI上下文
        chat_history = await get_recent_chat_history(current_user.id, db, limit=5)
            
        # 保存用户消息
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            type=MessageType.text,
            content=message,
            is_user=True,
            created_at=datetime.now()
        )
        db.add(user_message)
        await db.commit()
        
        # 构建完整的消息列表
        messages = ai_client._build_chat_messages(
            user_profile=user_profile,
            current_message=message,
            chat_history=chat_history
        )
        
        # 创建流式响应
        async def generate_response():
            full_content = []
            async for chunk in ai_client.chat_stream(
                messages=messages,
                model="qwen2.5:14b"
            ):
                full_content.append(chunk)
                yield f"data: {chunk}\n\n"
                
            # 保存完整的系统响应
            system_message = ChatMessage(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                type=MessageType.text,
                content="".join(full_content),
                is_user=False,
                created_at=datetime.now()
            )
            db.add(system_message)
            await db.commit()
            
            # 获取用于响应的历史消息
            history = await get_chat_history_for_response(current_user.id, db)
            
            # 发送完整的消息历史
            yield f"data: {{'type': 'history', 'data': {history}}}\n\n"
            
        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"流式文本处理失败: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"流式文本处理失败: {str(e)}"
        )

async def get_user_profile(user_id: str, db: AsyncSession) -> Dict[str, Any]:
    """获取用户画像信息
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        
    Returns:
        Dict[str, Any]: 用户画像信息
    """
    # 从数据库获取用户画像信息
    query = select(UserProfileModel).filter(UserProfileModel.user_id == user_id)
    result = await db.execute(query)
    profile = result.scalar_one_or_none()
    
    if not profile:
        return {}  # 返回空画像
        
    return {
        # 基本信息
        "gender": profile.gender,
        "age": (datetime.now().date() - profile.birth_date).days // 365 if profile.birth_date else None,
        
        # 健康信息
        "height": profile.height,  # 厘米
        "weight": profile.weight,  # 千克
        "bmi": round(profile.weight / ((profile.height/100) ** 2), 1) if profile.height and profile.weight else None,
        "body_fat_percentage": profile.body_fat_percentage,
        "health_conditions": profile.health_conditions or [],
        "health_goals": profile.health_goals or [],
        
        # 饮食相关
        "food_preferences": profile.favorite_cuisines or [],
        "dietary_restrictions": profile.dietary_restrictions or [],
        "allergies": profile.allergies or [],
        "cooking_level": profile.cooking_skill_level or "初级",
        "calorie_preference": profile.calorie_preference,
        "nutrition_goals": profile.nutrition_goals or [],
        
        # 健身相关
        "fitness_level": profile.fitness_level,
        "exercise_frequency": profile.exercise_frequency,  # 每周运动次数
        "fitness_goals": profile.fitness_goals or []
    }

async def get_recent_chat_history(
    user_id: str,
    db: AsyncSession,
    limit: int = 5
) -> List[Dict[str, str]]:
    """获取最近的聊天历史
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        limit: 获取的消息数量
        
    Returns:
        List[Dict[str, str]]: 聊天历史记录
    """
    # 获取最近的消息
    query = (
        select(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    messages = result.scalars().all()
    
    # 转换为LLM消息格式
    chat_history = []
    for msg in reversed(messages):  # 反转顺序，使其按时间正序
        role = "user" if msg.is_user else "assistant"
        chat_history.append({
            "role": role,
            "content": msg.content
        })
        
    return chat_history

@router.post("/voice", response_model=MessageResponse)
@limiter.limit("60/minute")
async def voice_chat(
    request: Request,
    file: UploadFile = File(...),
    voice_request: VoiceRequest = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """处理语音聊天请求"""
    try:
        # 验证文件大小和类型
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"文件大小不能超过{MAX_FILE_SIZE/1024/1024}MB"
            )
            
        if file.content_type not in ALLOWED_AUDIO_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的音频格式: {file.content_type}"
            )
            
        # 读取文件内容
        content = await file.read()
        
        # 转写语音内容
        transcribed_text = await ai_client.process_voice(content)
        
        # 获取用户画像
        user_profile = await get_user_profile(current_user.id, db)
        
        # 获取最近的聊天历史
        chat_history = await get_recent_chat_history(current_user.id, db, limit=5)
        
        # 保存用户消息
        voice_url = await file_service.save_file(content, VOICE_DIR, file.filename)
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            type=MessageType.voice,
            content=transcribed_text,
            voice_url=voice_url,
            is_user=True,
            created_at=datetime.now()
        )
        db.add(user_message)
        
        # 构建完整的消息列表
        messages = ai_client._build_chat_messages(
            user_profile=user_profile,
            current_message=transcribed_text,
            chat_history=chat_history
        )
        
        # 获取AI响应
        chat_response = await ai_client.chat(
            messages=messages,
            model="qwen2.5:14b"
        )
        
        content = chat_response.get("response", "")
        if not content:
            raise ValueError("AI响应内容为空")
            
        # 保存系统响应
        system_message = ChatMessage(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            type=MessageType.text,
            content=content,
            is_user=False,
            created_at=datetime.now()
        )
        db.add(system_message)
        await db.commit()
        
        # 获取用于响应的历史消息
        history = await get_chat_history_for_response(current_user.id, db)
        
        return MessageResponse(
            schema_version="1.0",
            message=content,
            voice_url=voice_url,
            transcribed_text=transcribed_text,
            created_at=system_message.created_at,
            history=history
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"语音处理失败: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"语音处理失败: {str(e)}"
        )

@router.post("/food", response_model=MessageResponse)
@limiter.limit("60/minute")
async def food_recognition(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """处理食物识别请求"""
    try:
        # 验证文件大小和类型
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"文件大小不能超过{MAX_FILE_SIZE/1024/1024}MB"
            )
            
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的图片格式: {file.content_type}"
            )
            
        # 读取文件内容并转换为base64
        content = await file.read()
        image_base64 = base64.b64encode(content).decode('utf-8')
        
        # 保存图片
        image_url = await file_service.save_file(content, IMAGE_DIR, file.filename)
        
        # 识别食物
        recognition_result = await ai_client.recognize_food(image_base64)
        
        if not recognition_result.get("success", False):
            raise HTTPException(
                status_code=500,
                detail=recognition_result.get("message", "食物识别失败")
            )
            
        # 保存用户消息
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            type=MessageType.image,
            content="[食物图片]",
            image_url=image_url,
            is_user=True,
            created_at=datetime.now()
        )
        db.add(user_message)
        
        # 构建响应消息
        food_items = recognition_result.get("food_items", [])
        content = "我识别到以下食物：\n" + "\n".join(
            f"- {item.get('name', '未知食物')}" 
            for item in food_items
        )
        
        # 保存系统响应
        system_message = ChatMessage(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            type=MessageType.text,
            content=content,
            is_user=False,
            created_at=datetime.now()
        )
        db.add(system_message)
        await db.commit()
        
        return MessageResponse(
            schema_version="1.0",
            message=content,
            image_url=image_url,
            food_items=food_items,
            created_at=system_message.created_at
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"食物识别失败: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"食物识别失败: {str(e)}"
        )

@router.post("/image", response_model=MessageResponse)
@limiter.limit("60/minute")
async def image_chat(
    request: Request,
    file: UploadFile = File(...),
    image_request: ImageRequest = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """处理图片消息"""
    try:
        # 验证并获取文件内容
        content = await file_service._verify_file_type(
            file, 
            file_service.ALLOWED_IMAGE_TYPES,
            "不支持的图片格式"
        )
        
        # 验证文件大小
        if len(content) > file_service.MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制: {file_service.MAX_IMAGE_SIZE/1024/1024:.1f}MB"
            )
        
        # 保存图片文件
        image_url = await file_service.save_image(file)
        
        # 处理图片消息
        result = await process_image(content, image_url, current_user, db)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理图片消息时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="处理图片消息时发生错误"
        )

@router.get("/history", response_model=MessageHistory)
async def get_chat_history(
    page: int = Query(1, gt=0),
    per_page: int = Query(20, gt=0, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取聊天历史记录"""
    try:
        # 构建基础查询
        base_query = select(ChatMessage).filter(
            ChatMessage.user_id == current_user.id
        )
        
        # 添加日期过滤
        if start_date:
            base_query = base_query.filter(ChatMessage.created_at >= start_date)
        if end_date:
            base_query = base_query.filter(ChatMessage.created_at <= end_date)
            
        # 获取总数
        total_query = select(func.count()).select_from(
            base_query.subquery()
        )
        total = await db.scalar(total_query) or 0
        
        # 计算总页数
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        
        # 获取分页数据
        query = base_query.order_by(ChatMessage.created_at.desc())
        result = await db.execute(
            query.offset((page - 1) * per_page).limit(per_page)
        )
        messages = result.scalars().all()
        
        # 构建消息列表
        message_list = []
        for msg in messages:
            suggestions = []
            if msg.suggestions:
                suggestions = [s.strip() for s in msg.suggestions.split(",") if s.strip()]
                
            message_response = MessageResponse(
                schema_version="1.0",
                message=msg.content,
                suggestions=suggestions,
                voice_url=msg.voice_url,
                image_url=msg.image_url,
                transcribed_text=msg.transcribed_text,
                analysis_result=msg.analysis_result,
                created_at=msg.created_at,
                is_user=msg.is_user
            )
            message_list.append(message_response)
        
        # 构建分页信息
        pagination_info = PaginationInfo(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages
        )
        
        # 构建最终响应
        return MessageHistory(
            schema_version="1.0",
            messages=message_list,
            pagination=pagination_info
        )
        
    except Exception as e:
        logger.error(f"获取聊天历史失败: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"获取聊天历史失败: {str(e)}"
        ) 