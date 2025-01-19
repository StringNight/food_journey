"""菜谱数据模型

存储菜谱的基本信息
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import json

from . import Base

class RecipeModel(Base):
    """菜谱数据模型
    
    存储菜谱的基本信息和关联数据
    """
    
    __tablename__ = 'recipes'
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    ingredients = Column(JSON, nullable=False)  # [{"name": "...", "amount": "..."}]
    steps = Column(JSON, nullable=False)  # [{"step": 1, "description": "..."}]
    cooking_time = Column(Integer)  # 分钟
    difficulty = Column(String)  # "简单", "中等", "困难"
    cuisine_type = Column(String)  # "中餐", "西餐", "日料" 等
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    views_count = Column(Integer, default=0)  # 浏览次数
    average_rating = Column(Float, default=0.0)  # 平均评分
    
    # 关系
    author = relationship("User", back_populates="recipes")
    ratings = relationship("RatingModel", back_populates="recipe")
    favorites = relationship("FavoriteModel", back_populates="recipe", cascade="all, delete-orphan")
    
    @classmethod
    def from_recipe(cls, recipe):
        """从Recipe模式对象创建数据库模型实例"""
        return cls(
            id=recipe.id,
            title=recipe.title,
            description=recipe.description,
            author_id=recipe.author_id,
            ingredients=json.loads(json.dumps(recipe.ingredients)),
            steps=json.loads(json.dumps(recipe.steps)),
            cooking_time=recipe.cooking_time,
            difficulty=recipe.difficulty,
            cuisine_type=recipe.cuisine_type
        ) 