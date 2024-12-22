from typing import List, Dict, Any, Optional
from datetime import datetime
from .models.user import User
from sqlalchemy.orm import Session
import logging

class UserProfile:
    """用户画像管理类，作为 User 模型的业务逻辑封装"""
    
    def __init__(self, user: User, db: Session):
        self.user = user
        self.db = db
    
    @property
    def favorite_cuisines(self) -> List[str]:
        return self.user.cooking_preferences.get('favorite_cuisines', [])
    
    @favorite_cuisines.setter
    def favorite_cuisines(self, cuisines: List[str]):
        self._update_cooking_preferences({'favorite_cuisines': cuisines})
    
    @property
    def dietary_restrictions(self) -> List[str]:
        return self.user.dietary_restrictions.get('restrictions', [])
    
    @dietary_restrictions.setter
    def dietary_restrictions(self, restrictions: List[str]):
        self._update_profile_value('dietary_restrictions', {'restrictions': restrictions})
    
    @property
    def allergies(self) -> List[str]:
        return self.user.dietary_restrictions.get('allergies', [])
    
    @allergies.setter
    def allergies(self, allergies: List[str]):
        self._update_profile_value('dietary_restrictions', {'allergies': allergies})
    
    @property
    def cooking_skill_level(self) -> str:
        return self.user.cooking_preferences.get('skill_level', 'beginner')
    
    @cooking_skill_level.setter
    def cooking_skill_level(self, level: str):
        self._update_cooking_preferences({'skill_level': level})
    
    @property
    def calorie_preference(self) -> Optional[int]:
        return self.user.health_data.get('calorie_preference')
    
    @calorie_preference.setter
    def calorie_preference(self, calories: Optional[int]):
        self._update_profile_value('health_data', {'calorie_preference': calories})
    
    @property
    def health_goals(self) -> List[str]:
        return self.user.health_data.get('goals', [])
    
    @health_goals.setter
    def health_goals(self, goals: List[str]):
        self._update_profile_value('health_data', {'goals': goals})
    
    def _update_cooking_preferences(self, data: Dict[str, Any]):
        """更新烹饪偏好"""
        try:
            current_prefs = self.user.cooking_preferences
            current_prefs.update(data)
            self.user.set_profile_value('cooking_preferences', current_prefs)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logging.error(f"更新烹饪偏好失败: {e}")
            raise
    
    def _update_profile_value(self, category: str, data: Dict[str, Any]):
        """更新指定类别的数据"""
        try:
            current_data = self.user.get_profile_value(category, {})
            current_data.update(data)
            self.user.set_profile_value(category, current_data)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logging.error(f"更新用户画像失败: {e}")
            raise
    
    def update_preferences(self, **kwargs):
        """更新用户偏好"""
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        except Exception as e:
            logging.error(f"更新用户偏好失败: {e}")
            raise
    
    def log_interaction(self, interaction_type: str, data: Dict[str, Any]):
        """记录用户交互"""
        try:
            history = self.user.interaction_history
            if 'interactions' not in history:
                history['interactions'] = []
            
            history['interactions'].append({
                'type': interaction_type,
                'data': data,
                'timestamp': datetime.now().isoformat()
            })
            
            # 保持最近的100条记录
            history['interactions'] = history['interactions'][-100:]
            self.user.set_profile_value('interaction_history', history)
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logging.error(f"记录用户交互失败: {e}")
            raise
    
    def get_nutrition_summary(self) -> Dict[str, Any]:
        """获取营养摄入总结"""
        return self.user.health_data.get('nutrition_summary', {})
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'user_id': self.user.id,
            'favorite_cuisines': self.favorite_cuisines,
            'dietary_restrictions': self.dietary_restrictions,
            'allergies': self.allergies,
            'cooking_skill_level': self.cooking_skill_level,
            'calorie_preference': self.calorie_preference,
            'health_goals': self.health_goals,
            'profile': self.user.profile  # 完整的用户画像数据
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], user: User, db: Session) -> 'UserProfile':
        """从字典创建用户画像"""
        profile = cls(user, db)
        profile.update_preferences(**data)
        return profile