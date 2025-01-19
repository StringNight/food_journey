from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import field_validator

class RecipeBase(BaseModel):
    """菜谱基础模型"""
    title: str = Field(..., min_length=1, max_length=100, description="菜谱标题")
    description: str = Field(..., min_length=1, max_length=1000, description="菜谱描述")
    ingredients: list[dict] = Field(..., max_length=50, description="食材列表")
    steps: list[dict] = Field(..., max_length=30, description="步骤列表")
    cooking_time: int = Field(..., gt=0, lt=1000, description="烹饪时间(分钟)")
    difficulty: str = Field(..., description="难度等级")
    cuisine_type: str = Field(..., description="菜系类型")

    @field_validator("ingredients")
    def validate_ingredients(cls, v):
        if len(v) > 50:
            raise ValueError("食材数量不能超过50个")
        for item in v:
            if not isinstance(item, dict) or "name" not in item or "amount" not in item:
                raise ValueError("食材格式错误")
            if len(item["name"]) > 50 or len(item["amount"]) > 20:
                raise ValueError("食材名称或数量过长")
        return v

    @field_validator("steps")
    def validate_steps(cls, v):
        if len(v) > 30:
            raise ValueError("步骤数量不能超过30个")
        for item in v:
            if not isinstance(item, dict) or "step" not in item or "description" not in item:
                raise ValueError("步骤格式错误")
            if len(item["description"]) > 500:
                raise ValueError("步骤描述过长")
        return v

    @field_validator("difficulty")
    def validate_difficulty(cls, v):
        valid_difficulties = ["简单", "中等", "困难"]
        if v not in valid_difficulties:
            raise ValueError("无效的难度等级")
        return v

    @field_validator("cuisine_type")
    def validate_cuisine_type(cls, v):
        valid_types = ["中餐", "西餐", "日料", "韩餐", "其他"]
        if v not in valid_types:
            raise ValueError("无效的菜系类型")
        return v

class RecipeCreate(RecipeBase):
    """创建食谱的请求模型"""
    pass

class RecipeUpdate(BaseModel):
    """更新食谱的请求模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=100, description="食谱标题")
    description: Optional[str] = Field(None, min_length=1, max_length=1000, description="食谱描述")
    ingredients: Optional[list[dict]] = Field(None, max_length=50, description="食材列表")
    steps: Optional[list[dict]] = Field(None, max_length=30, description="步骤列表")
    cooking_time: Optional[int] = Field(None, gt=0, lt=1000, description="烹饪时间(分钟)")
    difficulty: Optional[str] = Field(None, description="难度等级")
    cuisine_type: Optional[str] = Field(None, description="菜系类型")

    @field_validator("ingredients")
    def validate_ingredients(cls, v):
        if v is None:
            return v
        if len(v) > 50:
            raise ValueError("食材数量不能超过50个")
        for item in v:
            if not isinstance(item, dict) or "name" not in item or "amount" not in item:
                raise ValueError("食材格式错误")
            if len(item["name"]) > 50 or len(item["amount"]) > 20:
                raise ValueError("食材名称或数量过长")
        return v

    @field_validator("steps")
    def validate_steps(cls, v):
        if v is None:
            return v
        if len(v) > 30:
            raise ValueError("步骤数量不能超过30个")
        for item in v:
            if not isinstance(item, dict) or "step" not in item or "description" not in item:
                raise ValueError("步骤格式错误")
            if len(item["description"]) > 500:
                raise ValueError("步骤描述过长")
        return v

    @field_validator("difficulty")
    def validate_difficulty(cls, v):
        if v is None:
            return v
        valid_difficulties = ["简单", "中等", "困难"]
        if v not in valid_difficulties:
            raise ValueError("无效的难度等级")
        return v

    @field_validator("cuisine_type")
    def validate_cuisine_type(cls, v):
        if v is None:
            return v
        valid_types = ["中餐", "西餐", "日料", "韩餐", "其他"]
        if v not in valid_types:
            raise ValueError("无效的菜系类型")
        return v

class Recipe(RecipeBase):
    """完整食谱模型"""
    id: str = Field(..., description="食谱ID")
    author_id: str = Field(..., description="作者ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    views_count: int = Field(0, description="浏览次数")
    average_rating: Optional[float] = Field(0.0, description="平均评分")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class RecipeResponse(BaseModel):
    """食谱响应模型"""
    schema_version: str = "1.0"
    recipe: Recipe

class PaginationInfo(BaseModel):
    """分页信息模型"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    per_page: int = Field(..., description="每页记录数")
    pages: int = Field(..., description="总页数")

class RecipeListResponse(BaseModel):
    """食谱列表响应模型"""
    schema_version: str = "1.0"
    recipes: List[Recipe]
    pagination: PaginationInfo = Field(..., description="分页信息")

class RecipeSearchParams(BaseModel):
    """食谱搜索参数模型"""
    page: int = Field(1, gt=0, description="页码")
    per_page: int = Field(20, gt=0, le=100, description="每页数量")
    difficulty: Optional[str] = Field(None, description="难度过滤")
    cooking_time: Optional[int] = Field(None, description="烹饪时间过滤（分钟）")
    cuisine_type: Optional[str] = Field(None, description="菜系过滤")

class RatingCreate(BaseModel):
    """创建评分的请求模型"""
    rating: float = Field(..., description="评分值", ge=1.0, le=5.0)
    comment: str = Field(None, description="评价内容")

    @field_validator("rating")
    def validate_rating(cls, v):
        if not 1.0 <= v <= 5.0:
            raise ValueError("评分必须在1到5之间")
        return v 