from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import uuid
from . import Base

class RatingModel(Base):
    """评分数据模型
    
    属性:
        id (str): 评分记录的唯一标识符，使用UUID自动生成
        user_id (str): 评分用户的ID，外键关联到users表
        recipe_id (str): 被评分菜谱的ID，外键关联到recipes表
        rating (float): 评分值，1.0到5.0之间的浮点数
        comment (str): 评价内容，可选
        created_at (datetime): 评分创建时间
        user (relationship): 与User模型的关系，表示评分的用户
        recipe (relationship): 与Recipe模型的关系，表示被评分的菜谱
    """
    
    __tablename__ = 'ratings'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'))
    recipe_id = Column(String, ForeignKey('recipes.id', ondelete='CASCADE'))
    rating = Column(Float, nullable=False)
    comment = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # 关系
    user = relationship("User", back_populates="ratings")
    recipe = relationship("RecipeModel", back_populates="ratings") 