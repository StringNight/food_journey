"""收藏数据模型

存储用户的菜谱收藏记录
"""

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from . import Base

class FavoriteModel(Base):
    """收藏数据模型
    
    存储用户对菜谱的收藏关系
    """
    
    __tablename__ = 'favorites'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    recipe_id = Column(String, ForeignKey("recipes.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    user = relationship("User", back_populates="favorites")
    recipe = relationship("RecipeModel", back_populates="favorites") 