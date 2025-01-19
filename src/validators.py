from pydantic import BaseModel, validator, Field
from typing import List, Dict, Optional
from datetime import datetime

class IngredientInput(BaseModel):
    """食材输入模型
    
    用于验证和规范化食材数据的输入格式
    """
    name: str = Field(..., min_length=1)  # 食材名称，不能为空
    amount: str = Field(..., min_length=1)  # 食材数量，不能为空
    unit: Optional[str] = None  # 计量单位，可选

class StepInput(BaseModel):
    """烹饪步骤输入模型
    
    用于验证和规范化烹饪步骤的输入格式
    """
    step_number: int = Field(..., ge=1)  # 步骤序号，必须大于等于1
    description: str = Field(..., min_length=5)  # 步骤描述，最少5个字符
    image: Optional[str] = None  # 步骤图片URL，可选
    tips: Optional[str] = None  # 烹饪技巧，可选

class NutritionInput(BaseModel):
    """营养信息输入模型
    
    用于验证和规范化营养信息的输入格式
    """
    calories: float = Field(..., ge=0)  # 卡路里，必须大于等于0
    protein: float = Field(..., ge=0)  # 蛋白质，必须大于等于0
    carbs: float = Field(..., ge=0)  # 碳水化合物，必须大于等于0
    fat: float = Field(..., ge=0)  # 脂肪，必须大于等于0
    fiber: Optional[float] = Field(None, ge=0)  # 膳食纤维，可选，如果提供必须大于等于0
    vitamins: Optional[Dict[str, float]] = None  # 维生素含量，可选

class RecipeInput(BaseModel):
    """菜谱输入模型
    
    用于验证和规范化菜谱的输入格式
    """
    title: str = Field(..., min_length=2)  # 菜谱标题，最少2个字符
    ingredients: List[IngredientInput]  # 食材列表
    steps: List[StepInput]  # 步骤列表
    nutrition: NutritionInput  # 营养信息
    cooking_time: Optional[int] = Field(None, ge=1)  # 烹饪时间（分钟），如果提供必须大于等于1
    difficulty: Optional[str] = Field(None, pattern="^(简单|中等|困难)$")  # 难度等级
    tags: Optional[List[str]] = None  # 标签列表

    @validator('title')
    def title_must_not_be_empty(cls, v):
        """验证标题不能为空
        
        Args:
            v: 标题值
            
        Returns:
            str: 处理后的标题
            
        Raises:
            ValueError: 当标题为空时抛出
        """
        if not v.strip():
            raise ValueError('标题不能为空')
        return v.strip()

    @validator('tags')
    def validate_tags(cls, v):
        """验证标签是否有效
        
        Args:
            v: 标签列表
            
        Returns:
            List[str]: 验证后的标签列表
            
        Raises:
            ValueError: 当存在无效标签时抛出
        """
        if v:
            valid_tags = {'快手菜', '低脂', '高蛋白', '素食', '早餐', '午餐', '晚餐', '小食'}
            invalid_tags = set(v) - valid_tags
            if invalid_tags:
                raise ValueError(f'无效的标签: {invalid_tags}')
        return v

class UserProfileInput(BaseModel):
    """用户画像输入模型
    
    用于验证和规范化用户画像的输入格式
    """
    favorite_cuisines: Optional[List[str]] = None  # 喜爱的菜系
    dietary_restrictions: Optional[List[str]] = None  # 饮食限制
    allergies: Optional[List[str]] = None  # 过敏源
    cooking_skill_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")  # 烹饪技能水平
    calorie_preference: Optional[int] = Field(None, ge=0)  # 卡路里偏好
    health_goals: Optional[List[str]] = None  # 健康目标

    @validator('favorite_cuisines')
    def validate_cuisines(cls, v):
        """验证菜系是否有效
        
        Args:
            v: 菜系列表
            
        Returns:
            List[str]: 验证后的菜系列表
            
        Raises:
            ValueError: 当存在无效菜系时抛出
        """
        if v:
            valid_cuisines = {'川菜', '粤菜', '湘菜', '鲁菜', '苏菜', '浙菜', '闽菜', '徽菜'}
            invalid_cuisines = set(v) - valid_cuisines
            if invalid_cuisines:
                raise ValueError(f'无效的菜系: {invalid_cuisines}')
        return v

class RatingInput(BaseModel):
    """评分输入模型
    
    用于验证和规范化用户评分的输入格式
    """
    recipe_id: str  # 菜谱ID
    rating: float = Field(..., ge=1, le=5)  # 评分，1-5分
    comment: Optional[str] = None  # 评论内容
    timestamp: datetime = Field(default_factory=datetime.now)  # 评分时间
  