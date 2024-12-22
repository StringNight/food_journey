from sqlalchemy import create_engine, Column, String, JSON, Integer, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json

Base = declarative_base()

class RecipeModel(Base):
    """菜谱数据模型
    
    存储菜谱的基本信息和关联数据
    """
    
    __tablename__ = 'recipes'
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    ingredients = Column(JSON, nullable=False)
    steps = Column(JSON, nullable=False)
    nutrition = Column(JSON, nullable=False)
    cooking_time = Column(Integer)
    difficulty = Column(String)
    tags = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    ratings = relationship("RatingModel", back_populates="recipe")
    
    @classmethod
    def from_recipe(cls, recipe):
        return cls(
            id=recipe.id,
            title=recipe.title,
            ingredients=json.loads(json.dumps(recipe.ingredients)),
            steps=json.loads(json.dumps(recipe.steps)),
            nutrition=json.loads(json.dumps(recipe.nutrition)),
            cooking_time=recipe.cooking_time,
            difficulty=recipe.difficulty,
            tags=recipe.tags
        )

class UserProfileModel(Base):
    """用户画像数据模型
    
    存储用户的偏好设置和个性化数据
    """
    
    __tablename__ = 'user_profiles'
    
    id = Column(String, primary_key=True)
    favorite_cuisines = Column(JSON)
    dietary_restrictions = Column(JSON)
    allergies = Column(JSON)
    cooking_skill_level = Column(String)
    calorie_preference = Column(Integer)
    health_goals = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    ratings = relationship("RatingModel", back_populates="user")
    nutrition_records = relationship("NutritionRecordModel", back_populates="user")

class RatingModel(Base):
    """评分数据模型
    
    存储用户对菜谱的评分信息
    """
    
    __tablename__ = 'ratings'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('user_profiles.id'))
    recipe_id = Column(String, ForeignKey('recipes.id'))
    rating = Column(Float, nullable=False)
    comment = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    user = relationship("UserProfileModel", back_populates="ratings")
    recipe = relationship("RecipeModel", back_populates="ratings")

class NutritionRecordModel(Base):
    """营养记录数据模型
    
    存储用户的营养摄入记录
    """
    
    __tablename__ = 'nutrition_records'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('user_profiles.id'))
    recipe_id = Column(String, ForeignKey('recipes.id'))
    nutrition_data = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    
    # 关系
    user = relationship("UserProfileModel", back_populates="nutrition_records") 