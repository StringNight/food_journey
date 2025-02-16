from sqlalchemy import Column, String, Float, Integer, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base
from uuid import uuid4

class FoodItem(Base):
    """食物项目数据库模型"""
    __tablename__ = "food_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    meal_id = Column(String, ForeignKey("meal_records.id"), nullable=False)
    food_name = Column(String, nullable=False)
    portion = Column(Float, nullable=False)
    calories = Column(Float, nullable=False)
    protein = Column(Float)
    carbs = Column(Float)
    fat = Column(Float)
    fiber = Column(Float)
    
    # 关系
    meal = relationship("MealRecord", back_populates="food_items")

class MealRecord(Base):
    """餐食记录数据库模型"""
    __tablename__ = "meal_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    meal_type = Column(String, nullable=False)
    total_calories = Column(Float, nullable=False)
    location = Column(String)
    mood = Column(String)
    notes = Column(String)
    recorded_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # 关系
    food_items = relationship("FoodItem", back_populates="meal")
    user = relationship("User", back_populates="meal_records")

class DailyNutritionSummary(Base):
    """每日营养摄入汇总数据库模型"""
    __tablename__ = "daily_nutrition_summaries"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    total_calories = Column(Float, default=0)
    total_protein = Column(Float, default=0)
    total_carbs = Column(Float, default=0)
    total_fat = Column(Float, default=0)
    total_fiber = Column(Float, default=0)
    net_calories = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="nutrition_summaries") 