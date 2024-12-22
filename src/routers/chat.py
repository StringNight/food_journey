from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import aiofiles
import uuid
from datetime import datetime

from src.database import get_db
from src.models.chat import Message, MessageType
from src.schemas.chat import MessageResponse, TextRequest, ImageRequest, VoiceRequest, MessageHistory
from src.auth.jwt import get_current_user
from src.models.user import User
from src.llm_handler import LLMHandler
from src.voice_processor import VoiceProcessor

router = APIRouter()
llm_handler = LLMHandler()
voice_processor = VoiceProcessor()

@router.post("/text", response_model=MessageResponse)
async def process_text(
    request: TextRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 保存用户消息
    user_message = Message(
        user_id=current_user.id,
        type=MessageType.text,
        content=request.message,
        is_user=True
    )
    db.add(user_message)
    
    # 获取用户档案
    user_profile = {
        "cooking_skill_level": current_user.cooking_skill_level,
        "favorite_cuisines": current_user.favorite_cuisines,
        "dietary_restrictions": current_user.dietary_restrictions,
        "allergies": current_user.allergies,
        "calorie_preference": current_user.calorie_preference,
        "health_goals": current_user.health_goals
    }
    
    # 获取 LLM 响应
    response = await llm_handler.process_chat_message(request.message, user_profile)
    
    # 保存系统响应
    system_message = Message(
        user_id=current_user.id,
        type=MessageType.text,
        content=response.message,
        is_user=False,
        image_url=response.image_url,
        voice_url=response.voice_url
    )
    db.add(system_message)
    db.commit()
    
    return response

@router.post("/image", response_model=MessageResponse)
async def process_image(
    request: ImageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 保存用户消息
    user_message = Message(
        user_id=current_user.id,
        type=MessageType.image,
        content="",
        is_user=True,
        image_url=request.image_url
    )
    db.add(user_message)
    
    # 获取用户档案
    user_profile = {
        "cooking_skill_level": current_user.cooking_skill_level,
        "favorite_cuisines": current_user.favorite_cuisines,
        "dietary_restrictions": current_user.dietary_restrictions,
        "allergies": current_user.allergies,
        "calorie_preference": current_user.calorie_preference,
        "health_goals": current_user.health_goals
    }
    
    # 获取 LLM 响应
    response = await llm_handler.process_chat_message(f"分析这张图片: {request.image_url}", user_profile)
    
    # 保存系统响应
    system_message = Message(
        user_id=current_user.id,
        type=MessageType.text,
        content=response.message,
        is_user=False,
        image_url=response.image_url,
        voice_url=response.voice_url
    )
    db.add(system_message)
    db.commit()
    
    return response

@router.post("/voice", response_model=MessageResponse)
async def process_voice(
    request: VoiceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 使用voice_processor处理语音
        transcribed_text = await voice_processor.process_voice(request.voice_url)
        
        # 保存用户消息
        user_message = Message(
            user_id=current_user.id,
            type=MessageType.voice,
            content=transcribed_text,  # 保存转录的文本
            is_user=True,
            voice_url=request.voice_url
        )
        db.add(user_message)
        
        # 获取用户档案
        user_profile = {
            "cooking_skill_level": current_user.cooking_skill_level,
            "favorite_cuisines": current_user.favorite_cuisines,
            "dietary_restrictions": current_user.dietary_restrictions,
            "allergies": current_user.allergies,
            "calorie_preference": current_user.calorie_preference,
            "health_goals": current_user.health_goals
        }
        
        # 获取 LLM 响应
        response = await llm_handler.process_chat_message(transcribed_text, user_profile)
        
        # 保存系统响应
        system_message = Message(
            user_id=current_user.id,
            type=MessageType.text,
            content=response.message,
            is_user=False,
            image_url=response.image_url,
            voice_url=response.voice_url
        )
        db.add(system_message)
        db.commit()
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"语音处理失败: {str(e)}"
        )

@router.get("/history", response_model=MessageHistory)
async def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    messages = db.query(Message).filter(
        Message.user_id == current_user.id
    ).order_by(Message.created_at.desc()).limit(50).all()
    
    return MessageHistory(messages=messages) 