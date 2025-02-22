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
            profile = self.db.query(UserProfileModel).filter(UserProfileModel.user_id == user_id).first()

            if profile:
                # 返回完整的用户画像数据，包括基本信息、健康信息、饮食偏好、健身信息和扩展属性
                return {
                    "user_id": profile.user_id,
                    "birth_date": profile.birth_date.isoformat() if profile.birth_date else None,
                    "gender": profile.gender,
                    "nickname": profile.nickname,
                    "age": profile.age,
                    "height": profile.height,
                    "weight": profile.weight,
                    "body_fat_percentage": profile.body_fat_percentage,
                    "muscle_mass": profile.muscle_mass,
                    "bmr": profile.bmr,
                    "tdee": profile.tdee,
                    "bmi": profile.bmi,
                    "water_ratio": profile.water_ratio,
                    "health_conditions": profile.health_conditions,
                    "health_goals": profile.health_goals,
                    "cooking_skill_level": profile.cooking_skill_level,
                    "favorite_cuisines": profile.favorite_cuisines,
                    "dietary_restrictions": profile.dietary_restrictions,
                    "allergies": profile.allergies,
                    "calorie_preference": profile.calorie_preference,
                    "fitness_level": profile.fitness_level,
                    "exercise_frequency": profile.exercise_frequency,
                    "preferred_exercises": profile.preferred_exercises,
                    "short_term_goals": profile.short_term_goals,
                    "long_term_goals": profile.long_term_goals,
                    "goal_progress": profile.goal_progress,
                    "training_type": profile.training_type,
                    "training_progress": profile.training_progress,
                    "muscle_group_analysis": profile.muscle_group_analysis,
                    "sleep_duration": profile.sleep_duration,
                    "deep_sleep_percentage": profile.deep_sleep_percentage,
                    "fatigue_score": profile.fatigue_score,
                    "recovery_activities": profile.recovery_activities,
                    "performance_metrics": profile.performance_metrics,
                    "exercise_history": profile.exercise_history,
                    "training_time_preference": profile.training_time_preference,
                    "equipment_preferences": profile.equipment_preferences,
                    "extended_attributes": profile.extended_attributes,
                    "created_at": profile.created_at.isoformat() if profile.created_at else None,
                    "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
                }
            return None
        except Exception as e:
            self.logger.error(f"获取用户画像失败: {str(e)}")
            return None
    
    def update_profile(self, user_id: str, profile_data: dict) -> bool:
        """更新用户画像
        采用传入的字典批量更新用户画像数据，支持更新新增的所有字段

        Args:
            user_id: 用户ID
            profile_data: 包含需要更新的字段及其值的字典，例如：{
                "cooking_skill_level": "advanced",
                "favorite_cuisines": ["中餐", "意大利菜"],
                ...
            }

        Returns:
            bool: 更新是否成功
        """
        try:
            profile = self.db.query(UserProfileModel).filter(UserProfileModel.user_id == user_id).first()

            if not profile:
                # 如果用户画像不存在，则根据传入数据创建一条新的记录
                profile = UserProfileModel(user_id=user_id, **profile_data)
                self.db.add(profile)
            else:
                # 批量更新已有记录
                for key, value in profile_data.items():
                    setattr(profile, key, value)

            self.db.commit()
            return True
        except Exception as e:
            self.logger.error(f"更新用户画像失败: {str(e)}")
            self.db.rollback()
            return False 