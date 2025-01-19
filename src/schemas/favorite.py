"""收藏相关的数据模型

包含收藏操作和列表的响应模型
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from ..schemas.recipe import Recipe

class FavoriteBase(BaseModel):
    """收藏基础模型
    
    Attributes:
        recipe_id (str): 食谱ID
        created_at (datetime): 收藏创建时间
    """
    recipe_id: str = Field(..., description="食谱ID")
    created_at: datetime = Field(..., description="收藏创建时间")

    class Config:
        from_attributes = True

class FavoriteResponse(BaseModel):
    """收藏操作响应模型
    
    Attributes:
        schema_version (str): API版本号,默认为"1.0"
        message (str): 操作结果消息
        recipe_id (str): 收藏的食谱ID
        created_at (datetime): 收藏创建时间
    """
    schema_version: str = Field(default="1.0", description="API版本号")
    message: str = Field(..., description="操作结果消息")
    recipe_id: str = Field(..., description="收藏的食谱ID")
    created_at: datetime = Field(..., description="收藏创建时间")

    class Config:
        from_attributes = True

class PaginationInfo(BaseModel):
    """分页信息模型
    
    Attributes:
        total (int): 总记录数
        page (int): 当前页码
        per_page (int): 每页记录数
        total_pages (int): 总页数
    """
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    per_page: int = Field(..., description="每页记录数")
    total_pages: int = Field(..., description="总页数")

class FavoriteRecipe(Recipe):
    """带有收藏信息的菜谱模型
    
    继承自Recipe模型,添加了收藏时间字段
    
    Attributes:
        created_at (datetime): 收藏创建时间
    """
    created_at: datetime = Field(..., description="收藏创建时间")

    class Config:
        from_attributes = True
        populate_by_name = True

    @property
    def recipe_id(self) -> str:
        """返回菜谱ID"""
        return self.id

class FavoriteListResponse(BaseModel):
    """收藏列表响应模型
    
    Attributes:
        schema_version (str): API版本号,默认为"1.0"
        favorites (List[FavoriteRecipe]): 收藏的食谱列表
        pagination (PaginationInfo): 分页信息
    """
    schema_version: str = Field(default="1.0", description="API版本号")
    favorites: List[FavoriteRecipe] = Field(..., description="收藏的食谱列表")
    pagination: PaginationInfo = Field(..., description="分页信息")

    class Config:
        from_attributes = True

class BatchFavoriteRequest(BaseModel):
    """批量收藏请求模型
    
    Attributes:
        recipe_ids (List[str]): 要收藏的食谱ID列表,最多10个
    """
    recipe_ids: List[str] = Field(..., description="要收藏的食谱ID列表,最多10个")

    class Config:
        json_schema_extra = {
            "example": {
                "recipe_ids": ["recipe-id-1", "recipe-id-2", "recipe-id-3"]
            }
        } 