from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from . import Base

class ExerciseType(str, enum.Enum):
    """运动类型枚举"""
    STRENGTH = "STRENGTH"  # 力量训练
    CARDIO = "CARDIO"     # 有氧运动
    FLEXIBILITY = "FLEXIBILITY"  # 柔韧性训练

class Workout(Base):
    """训练记录主表"""
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    workout_date = Column(DateTime, default=lambda: datetime.now(), nullable=False)
    name = Column(String, nullable=False, comment="训练计划名称")
    notes = Column(String, nullable=True, comment="训练备注")
    duration = Column(Integer, comment="训练时长(分钟)")
    created_at = Column(DateTime, default=lambda: datetime.now(), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now(), nullable=False)
    
    # 关联关系
    exercises = relationship("WorkoutExercise", back_populates="workout")
    user = relationship("User", back_populates="workouts")

class WorkoutExercise(Base):
    """训练记录详情表"""
    __tablename__ = "workout_exercises"

    id = Column(Integer, primary_key=True, index=True)
    workout_id = Column(Integer, ForeignKey("workouts.id"), nullable=False)
    exercise_type = Column(Enum(ExerciseType), nullable=False, comment="运动类型")
    exercise_name = Column(String, nullable=False, comment="运动项目名称")
    
    # 力量训练特有字段
    sets = Column(Integer, nullable=True, comment="组数")
    reps = Column(Integer, nullable=True, comment="每组重复次数")
    weight = Column(Float, nullable=True, comment="重量(千克)")
    
    # 有氧运动特有字段
    distance = Column(Float, nullable=True, comment="距离(公里)")
    speed = Column(Float, nullable=True, comment="速度(公里/小时)")
    
    # 通用字段
    duration = Column(Integer, nullable=True, comment="该项目持续时间(分钟)")
    calories = Column(Integer, nullable=True, comment="消耗卡路里")
    notes = Column(String, nullable=True, comment="该项目备注")
    
    # 关联关系
    workout = relationship("Workout", back_populates="exercises") 