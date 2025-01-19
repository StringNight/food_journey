from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from .database import get_db
from .models.user import User, UserProfileModel
import logging

class UserProfile:
    """用户画像管理器
    
    处理用户画像的创建、查询和更新等操作
    """
    
    def __init__(self):
        """初始化用户画像管理器"""
        self.logger = logging.getLogger(__name__)
        self.db = next(get_db())
    
    def get_profile(self, user_id: str) -> Optional[Dict]:
        """获取用户画像
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 用户画像，如果不存在则返回None
        """
        try:
            profile = self.db.query(UserProfileModel)\
                .filter(UserProfileModel.user_id == user_id)\
                .first()
            
            if profile:
                return {
                    "cooking_skill_level": profile.cooking_skill_level,
                    "favorite_cuisines": profile.favorite_cuisines,
                    "dietary_restrictions": profile.dietary_restrictions,
                    "allergies": profile.allergies,
                    "calorie_preference": profile.calorie_preference,
                    "health_goals": profile.health_goals
                }
            return None
        except Exception as e:
            self.logger.error(f"获取用户画像失败: {str(e)}")
            return None
    
    def update_profile(
        self,
        user_id: str,
        cooking_skill: str,
        preferred_cuisine: List[str],
        allergies: List[str],
        health_goals: List[str]
    ) -> bool:
        """更新用户画像
        
        Args:
            user_id: 用户ID
            cooking_skill: 烹饪技能水平
            preferred_cuisine: 偏好菜系
            allergies: 过敏源
            health_goals: 健康目标
            
        Returns:
            bool: 是否成功
        """
        try:
            profile = self.db.query(UserProfileModel)\
                .filter(UserProfileModel.user_id == user_id)\
                .first()
            
            if not profile:
                # 创建新的画像
                profile = UserProfileModel(
                    user_id=user_id,
                    cooking_skill_level=cooking_skill,
                    favorite_cuisines=preferred_cuisine,
                    dietary_restrictions=[],
                    allergies=allergies,
                    calorie_preference=2000,  # 默认值
                    health_goals=health_goals
                )
                self.db.add(profile)
            else:
                # 更新现有画像
                profile.cooking_skill_level = cooking_skill
                profile.favorite_cuisines = preferred_cuisine
                profile.allergies = allergies
                profile.health_goals = health_goals
            
            self.db.commit()
            return True
        except Exception as e:
            self.logger.error(f"更新用户画像失败: {str(e)}")
            self.db.rollback()
            return False 