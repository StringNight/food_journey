from typing import Dict, List, Optional
from datetime import datetime
import logging
import uuid

from .input_processor import InputProcessor
from .llm_handler import LLMHandler
from .user_profile import UserProfile
from .recipe_manager import RecipeManager
from .cache_manager import CacheManager, CachePrefix
from .async_handler import AsyncHandler
from .error_handler import ErrorHandler, error_handler
from .validators import RecipeInput, UserProfileInput, RatingInput

class FoodApp:
    def __init__(self):
        self.input_processor = InputProcessor()
        self.llm_handler = LLMHandler()
        self.recipe_manager = RecipeManager()
        self.cache_manager = CacheManager()
        self.async_handler = AsyncHandler()
        self.error_handler = ErrorHandler()
        self.user_profiles = {}

    def get_or_create_user_profile(self, user_id: str) -> UserProfile:
        """获取或创建用户档案"""
        # 先从缓存获取
        if cached_profile := self.cache_manager.get_cache(
            CachePrefix.USER_PROFILE, 
            user_id
        ):
            return UserProfile.from_dict(cached_profile)
        
        # 缓存未命中，创建新档案
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(user_id)
            # 保存到缓存
            self.cache_manager.set_cache(
                CachePrefix.USER_PROFILE,
                user_id,
                self.user_profiles[user_id].to_dict()
            )
        return self.user_profiles[user_id]

    @error_handler
    async def process_user_input(self, user_id: str, 
                               text: Optional[str] = None,
                               voice_file: Optional[bytes] = None,
                               image_file: Optional[bytes] = None,
                               chat_history: Optional[List[List[str]]] = None) -> Dict:
        """处理用户输入"""
        try:
            # 获取用户档案
            user_profile = self.get_or_create_user_profile(user_id)
            inputs = []
            
            if text:
                inputs.append(text)
            
            if voice_file:
                voice_text = self.input_processor.process_voice(voice_file)
                inputs.append(f"语音输入：{voice_text}")
            
            if image_file:
                image_desc = self.input_processor.process_image(image_file)
                response = self.llm_handler.get_response_with_image(
                    image_desc,
                    chat_history=chat_history,
                    user_profile=user_profile.to_dict()
                )
                
                # 记录交互
                user_profile.update_profile({
                    "type": "image_input",
                    "content": image_desc,
                    "response": response
                })
                
                return {"response": response}
            
            if not inputs:
                return {"error": "请提供至少一种输入"}
            
            combined_input = " ".join(inputs)
            response = self.llm_handler.get_response(
                combined_input,
                chat_history=chat_history,
                user_profile=user_profile.to_dict()
            )
            
            # 记录交互
            user_profile.update_profile({
                "type": "text_input",
                "content": combined_input,
                "response": response
            })
            
            return {"response": response}
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "function": "process_user_input",
                "user_id": user_id
            })
            return {"error": str(e)}

    @error_handler
    async def create_recipe(self, user_id: str, recipe_data: Dict) -> Optional[str]:
        """创建新菜谱"""
        try:
            # 验证数据
            validated_data = RecipeInput(**recipe_data)
            
            # 生成菜谱ID
            recipe_id = str(uuid.uuid4())
            validated_data_dict = validated_data.dict()
            validated_data_dict['id'] = recipe_id
            
            # 创建菜谱
            self.recipe_manager.create_recipe(validated_data_dict)
            
            # 更新用户档案
            user_profile = self.get_or_create_user_profile(user_id)
            user_profile.update_profile({
                "action": "create_recipe",
                "recipe_id": recipe_id,
                "timestamp": datetime.now().isoformat()
            })
            
            # 更新缓存
            self.cache_manager.set_cache(
                CachePrefix.RECIPE,
                recipe_id,
                validated_data_dict
            )
            
            return recipe_id
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "function": "create_recipe",
                "user_id": user_id,
                "recipe_data": recipe_data
            })
            return None

    @error_handler
    async def favorite_recipe(self, user_id: str, recipe_id: str) -> bool:
        """收藏菜谱"""
        try:
            user_profile = self.get_or_create_user_profile(user_id)
            success = user_profile.add_favorite(recipe_id)
            
            if success:
                # 更新缓存
                self.cache_manager.set_cache(
                    CachePrefix.USER_PROFILE,
                    user_id,
                    user_profile.to_dict()
                )
                
                # 记录交互
                user_profile.update_profile({
                    "action": "favorite_recipe",
                    "recipe_id": recipe_id,
                    "timestamp": datetime.now().isoformat()
                })
            
            return success
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "function": "favorite_recipe",
                "user_id": user_id,
                "recipe_id": recipe_id
            })
            return False

    @error_handler
    async def rate_recipe(self, user_id: str, recipe_id: str, 
                         rating: float, comment: Optional[str] = None) -> bool:
        """评分菜谱"""
        try:
            # 验证评分数据
            rating_data = RatingInput(
                recipe_id=recipe_id,
                rating=rating,
                comment=comment
            )
            
            # 更新菜谱评分
            self.recipe_manager.update_recipe_rating(recipe_id, rating)
            
            # 更新用户档案
            user_profile = self.get_or_create_user_profile(user_id)
            user_profile.update_profile({
                "action": "rate_recipe",
                "recipe_id": recipe_id,
                "rating": rating,
                "comment": comment,
                "timestamp": datetime.now().isoformat()
            })
            
            # 更新缓存
            self.cache_manager.delete_cache(CachePrefix.RECIPE, recipe_id)
            
            return True
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "function": "rate_recipe",
                "user_id": user_id,
                "recipe_id": recipe_id
            })
            return False

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
            self.cache_manager.set_cache(
                CachePrefix.USER_PROFILE,
                user_id,
                user_profile.to_dict()
            )
            
            return True
            
        except Exception as e:
            self.error_handler.log_error(e, {
                "function": "update_user_preferences",
                "user_id": user_id,
                "preferences": preferences
            })
            return False

    @error_handler
    async def get_nutrition_summary(self, user_id: str) -> Dict:
        """获取用户营养摄入总结"""
        try:
            user_profile = self.get_or_create_user_profile(user_id)
            return user_profile.get_nutrition_summary()
        except Exception as e:
            self.error_handler.log_error(e, {
                "function": "get_nutrition_summary",
                "user_id": user_id
            })
            return {}

    async def cleanup(self):
        """清理资源"""
        try:
            await self.async_handler.close()
            self.cache_manager.invalidate_popular_recipes()
        except Exception as e:
            logging.error(f"清理资源失败: {e}")