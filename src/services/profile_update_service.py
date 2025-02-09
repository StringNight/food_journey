"""
用户画像更新服务

负责从用户对话中提取信息并更新用户画像
"""

import logging
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
import uuid

from ..models.user import UserProfileModel
from ..services.ai_service_client import AIServiceClient

logger = logging.getLogger(__name__)

class ProfileUpdateService:
    def __init__(self):
        """初始化画像更新服务"""
        self.ai_client = AIServiceClient()
        
    async def process_user_interaction(
        self,
        user_id: str,
        user_message: str,
        ai_response: str,
        db: AsyncSession
    ) -> Dict:
        """处理用户交互，分析是否需要更新用户画像
        
        Args:
            user_id: 用户ID
            user_message: 用户的输入消息
            ai_response: AI的回复消息
            db: 数据库会话
            
        Returns:
            Dict: 处理结果，包含更新状态和相关信息
        """
        try:
            # 获取当前用户画像
            query = select(UserProfileModel).filter(UserProfileModel.user_id == user_id)
            result = await db.execute(query)
            profile = result.scalar_one_or_none()
            
            # 转换用户画像为字典格式
            profile_dict = None
            if profile:
                profile_dict = {
                    "health_conditions": profile.health_conditions,
                    "health_goals": profile.health_goals,
                    "favorite_cuisines": profile.favorite_cuisines,
                    "dietary_restrictions": profile.dietary_restrictions,
                    "allergies": profile.allergies,
                    "nutrition_goals": profile.nutrition_goals,
                    "fitness_level": profile.fitness_level,
                    "preferred_exercises": profile.preferred_exercises,
                    "fitness_goals": profile.fitness_goals
                }
            
            # 使用统一的提示词处理用户对话
            analysis_result = await self.ai_client.process_user_chat(
                user_message=user_message,
                ai_response=ai_response,
                user_profile=profile_dict
            )
            
            action = analysis_result.get("action", "chat")
            
            if action == "update":
                # 需要更新用户画像
                if not profile:
                    # 如果用户还没有画像，创建新的画像
                    profile = UserProfileModel(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        health_conditions=[],
                        health_goals=[],
                        favorite_cuisines=[],
                        dietary_restrictions=[],
                        allergies=[],
                        nutrition_goals=[],
                        fitness_level=None,
                        preferred_exercises=[],
                        fitness_goals=[],
                        extended_attributes={}
                    )
                    db.add(profile)
                
                # 更新用户画像
                profile_updates = analysis_result.get("profile_updates", {})
                for field, value in profile_updates.items():
                    if value and hasattr(profile, field):
                        if isinstance(value, list):
                            # 对于列表类型的字段，合并新旧值并去重
                            current_values = set(getattr(profile, field) or [])
                            new_values = set(value)
                            updated_values = list(current_values | new_values)
                            setattr(profile, field, updated_values)
                        else:
                            # 对于非列表类型的字段，直接更新
                            setattr(profile, field, value)
                
                profile.updated_at = datetime.now()
                await db.commit()
                return {
                    "action": "update",
                    "message": "用户画像已更新",
                    "profile_updates": profile_updates
                }
                
            elif action == "advice":
                # 用户需要建议
                if profile and not profile.extended_attributes:
                    profile.extended_attributes = {}
                if profile:
                    profile.extended_attributes["last_advice"] = analysis_result.get("advice", "")
                    profile.updated_at = datetime.now()
                    await db.commit()
                
                return {
                    "action": "advice",
                    "advice": analysis_result.get("advice", ""),
                    "message": "已生成个性化建议"
                }
            
            else:
                # 普通对话，不需要更新画像
                return {
                    "action": "chat",
                    "message": analysis_result.get("message", "处理完成")
                }
                
        except Exception as e:
            await db.rollback()
            logger.error(f"处理用户交互失败: {e}")
            return {
                "action": "error",
                "message": f"处理失败: {str(e)}"
            } 