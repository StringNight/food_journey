from sqlalchemy import Column, String, JSON, Integer, DateTime, Boolean, ForeignKey, Float, Date
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from . import Base

class User(Base):
    """用户基础数据模型
    
    存储用户的基本信息和认证数据
    """
    
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    avatar_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())
    last_login = Column(DateTime, nullable=True)  # 最后登录时间
    login_count = Column(Integer, default=0)  # 登录次数
    
    # 关系
    profile = relationship("UserProfileModel", back_populates="user", uselist=False)
    recipes = relationship("RecipeModel", back_populates="author", cascade="all, delete-orphan")
    favorites = relationship("FavoriteModel", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessageModel", back_populates="user", cascade="all, delete-orphan")
    ratings = relationship("RatingModel", back_populates="user", cascade="all, delete-orphan")
    meal_records = relationship("MealRecord", back_populates="user", cascade="all, delete-orphan")
    exercise_records = relationship("ExerciseRecord", back_populates="user", cascade="all, delete-orphan")
    nutrition_summaries = relationship("DailyNutritionSummary", back_populates="user", cascade="all, delete-orphan")

class UserProfileModel(Base):
    """用户画像数据模型
    
    存储用户的偏好设置和个性化数据，包括基本信息、健康信息、饮食偏好和健身信息
    """
    
    __tablename__ = 'user_profiles'
    
    # 基本信息
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), unique=True)
    birth_date = Column(Date)
    gender = Column(String)
    
    # 健康信息
    height = Column(Float)  # 身高（厘米）
    weight = Column(Float)  # 体重（千克）
    body_fat_percentage = Column(Float)  # 体脂率（%）
    muscle_mass = Column(Float)  # 肌肉量（千克）
    bmr = Column(Integer)  # 基础代谢率（卡路里）
    tdee = Column(Integer)  # 每日总能量消耗（卡路里）
    health_conditions = Column(JSON)  # 健康状况
    health_goals = Column(JSON)  # 健康目标
    
    # 饮食偏好
    cooking_skill_level = Column(String)  # 烹饪技能水平
    favorite_cuisines = Column(JSON)  # 喜好的菜系
    dietary_restrictions = Column(JSON)  # 饮食限制
    allergies = Column(JSON)  # 食物过敏
    calorie_preference = Column(Integer)  # 卡路里偏好
    nutrition_goals = Column(JSON)  # 营养目标
    
    # 健身信息
    fitness_level = Column(String)  # 健身水平
    exercise_frequency = Column(Integer)  # 每周运动频率
    preferred_exercises = Column(JSON)  # 偏好的运动类型
    fitness_goals = Column(JSON)  # 健身目标
    
    # 扩展属性
    extended_attributes = Column(JSON, default={})
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    user = relationship("User", back_populates="profile")

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "gender": self.gender,
            "height": self.height,
            "weight": self.weight,
            "body_fat_percentage": self.body_fat_percentage,
            "muscle_mass": self.muscle_mass,
            "bmr": self.bmr,
            "tdee": self.tdee,
            "health_conditions": self.health_conditions,
            "health_goals": self.health_goals,
            "cooking_skill_level": self.cooking_skill_level,
            "favorite_cuisines": self.favorite_cuisines,
            "dietary_restrictions": self.dietary_restrictions,
            "allergies": self.allergies,
            "calorie_preference": self.calorie_preference,
            "nutrition_goals": self.nutrition_goals,
            "fitness_level": self.fitness_level,
            "exercise_frequency": self.exercise_frequency,
            "preferred_exercises": self.preferred_exercises,
            "fitness_goals": self.fitness_goals,
            "extended_attributes": self.extended_attributes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict):
        """从字典创建实例"""
        if "birth_date" in data and isinstance(data["birth_date"], str):
            data["birth_date"] = datetime.fromisoformat(data["birth_date"]).date()
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)