from sqlalchemy import Column, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from . import Base

class NutritionRecordModel(Base):
    """营养记录数据模型
    
    存储用户的营养摄入记录
    """
    
    __tablename__ = 'nutrition_records'
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    recipe_id = Column(String, ForeignKey('recipes.id'))
    nutrition_data = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # 关系
    user = relationship("User", back_populates="nutrition_records") 