"""
用户服务模块

包含用户相关的所有业务逻辑，包括用户档案管理、偏好设置等功能
"""

from typing import Dict, Optional
from datetime import datetime, UTC
import logging
from ..models.user import UserProfileModel
from .cache_service import CacheService, CachePrefix
from .error_service import error_handler, ErrorService, ErrorCode
from ..validators import UserProfileInput

class UserService:
    def __init__(self):
        self.cache_service = CacheService()
        self.error_service = ErrorService()
        self.user_profiles = {}
        self.logger = logging.getLogger(__name__)

    def get_or_create_user_profile(self, user_id: str) -> UserProfileModel:
        """获取或创建用户档案"""
        try:
            # 先从缓存获取
            if cached_profile := self.cache_service.get(
                CachePrefix.USER_PROFILE, 
                user_id
            ):
                return UserProfileModel.from_dict(cached_profile)
            
            # 缓存未命中，创建新档案
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = UserProfileModel(user_id)
                # 保存到缓存
                self.cache_service.set(
                    CachePrefix.USER_PROFILE,
                    user_id,
                    self.user_profiles[user_id].to_dict()
                )
            return self.user_profiles[user_id]
            
        except Exception as e:
            self.error_service.log_error(e, {
                "function": "get_or_create_user_profile",
                "user_id": user_id
            })
            raise

    @error_handler
    async def update_user_preferences(self, user_id: str, preferences: Dict) -> bool:
        """更新用户偏好"""
        try:
            # 验证偏好数据
            validated_prefs = UserProfileInput(**preferences)
            
            # 更新用户档案
            user_profile = self.get_or_create_user_profile(user_id)
            user_profile.update_preferences(**validated_prefs.dict())
            
            # 更新缓存
            success = self.cache_service.set(
                CachePrefix.USER_PROFILE,
                user_id,
                user_profile.to_dict()
            )
            
            if not success:
                raise ValueError("更新缓存失败")
            
            return True
            
        except Exception as e:
            self.logger.error(f"更新用户偏好失败: {str(e)}")
            return False

    def update_user_interaction(self, user_id: str, interaction_data: Dict):
        """更新用户交互记录"""
        try:
            user_profile = self.get_or_create_user_profile(user_id)
            interaction_data["timestamp"] = datetime.now().isoformat()
            user_profile.update_profile(interaction_data)
            
            # 更新缓存
            success = self.cache_service.set(
                CachePrefix.USER_PROFILE,
                user_id,
                user_profile.to_dict()
            )
            
            if not success:
                raise ValueError("更新缓存失败")
                
        except Exception as e:
            self.error_service.log_error(e, {
                "function": "update_user_interaction",
                "user_id": user_id,
                "interaction_data": interaction_data
            }) 