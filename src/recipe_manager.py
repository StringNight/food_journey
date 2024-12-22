# src/recipe_manager.py
from typing import List, Dict, Optional
from .recipe import Recipe
import logging
from datetime import datetime

class RecipeManager:
    """菜谱管理器类
    
    负责菜谱的创建、查询、更新和删除操作
    """
    
    def __init__(self):
        """初始化菜谱管理器
        
        创建菜谱存储字典
        """
        self.recipes: Dict[str, Recipe] = {}
    
    def create_recipe(self, recipe_data: Dict) -> Optional[str]:
        """创建新菜谱
        
        Args:
            recipe_data: 菜谱数据字典
            
        Returns:
            Optional[str]: 成功返回菜谱ID，失败返回None
            
        Raises:
            Exception: 当创建失败时记录错误
        """
        try:
            recipe = Recipe.from_dict(recipe_data)
            self.recipes[recipe.id] = recipe
            return recipe.id
        except Exception as e:
            logging.error(f"创建菜谱失败: {e}")
            return None
    
    def get_recipe(self, recipe_id: str) -> Optional[Recipe]:
        """获取指定菜谱
        
        Args:
            recipe_id: 菜谱ID
            
        Returns:
            Optional[Recipe]: 找到返回菜谱对象，未找到返回None
        """
        return self.recipes.get(recipe_id)
    
    def search_recipes(self, query: Dict) -> List[Recipe]:
        """搜索菜谱
        
        Args:
            query: 搜索条件字典
            
        Returns:
            List[Recipe]: 符合条件的菜谱列表
        """
        # TODO: 实现搜索逻辑
        pass
    
    def update_recipe_rating(self, recipe_id: str, rating: float):
        """更新菜谱评分
        
        Args:
            recipe_id: 菜谱ID
            rating: 评分值
            
        Raises:
            KeyError: 当菜谱不存在时抛出
        """
        if recipe := self.recipes.get(recipe_id):
            recipe.ratings.append({
                "rating": rating,
                "timestamp": datetime.now()
            })