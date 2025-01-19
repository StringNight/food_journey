"""
食谱服务模块

包含食谱相关的所有业务逻辑，包括食谱的创建、管理、搜索等功能
"""

from typing import Dict, Optional, List
import uuid
from datetime import datetime
import logging
from .database_service import DatabaseService
from .error_service import error_handler, ErrorService
from ..validators import RecipeInput, RatingInput

class RecipeService:
    def __init__(self):
        self.db_service = DatabaseService()
        self.error_service = ErrorService()
        self.logger = logging.getLogger(__name__)
    
    async def init(self):
        """初始化服务"""
        await self.db_service.init_pool()
    
    @error_handler
    async def create_recipe(self, recipe_data: Dict) -> Optional[str]:
        """创建新菜谱"""
        try:
            # 验证数据
            validated_data = RecipeInput(**recipe_data)
            
            # 生成菜谱ID
            recipe_id = str(uuid.uuid4())
            validated_data_dict = validated_data.dict()
            validated_data_dict['id'] = recipe_id
            
            # 保存到数据库
            query = """
                INSERT INTO recipes (
                    id, title, description, ingredients, steps,
                    cooking_time, difficulty, cuisine_type,
                    author_id, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $10)
                RETURNING id
            """
            await self.db_service.execute(
                query,
                recipe_id,
                validated_data_dict['title'],
                validated_data_dict.get('description'),
                validated_data_dict['ingredients'],
                validated_data_dict['steps'],
                validated_data_dict.get('cooking_time'),
                validated_data_dict.get('difficulty', '简单'),
                validated_data_dict.get('cuisine_type'),
                validated_data_dict.get('author_id'),
                datetime.now()
            )
            
            return recipe_id
            
        except Exception as e:
            self.error_service.log_error(e, {
                "function": "create_recipe",
                "recipe_data": recipe_data
            })
            return None

    @error_handler
    async def rate_recipe(
        self,
        recipe_id: str,
        rating: float,
        user_id: str,
        comment: Optional[str] = None
    ) -> bool:
        """评分菜谱"""
        try:
            # 验证评分数据
            rating_data = RatingInput(
                recipe_id=recipe_id,
                rating=rating,
                user_id=user_id,
                comment=comment
            )
            
            # 检查菜谱是否存在
            query = "SELECT id FROM recipes WHERE id = $1"
            recipe = await self.db_service.fetch_one(query, recipe_id)
            if not recipe:
                return False
            
            # 保存评分到数据库
            query = """
                INSERT INTO ratings (
                    id, recipe_id, user_id, rating, comment, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """
            await self.db_service.execute(
                query,
                str(uuid.uuid4()),
                recipe_id,
                user_id,
                rating,
                comment,
                datetime.now()
            )
            
            # 更新平均评分
            query = """
                UPDATE recipes
                SET average_rating = (
                    SELECT AVG(rating)
                    FROM ratings
                    WHERE recipe_id = $1
                )
                WHERE id = $1
            """
            await self.db_service.execute(query, recipe_id)
            
            return True
            
        except Exception as e:
            self.error_service.log_error(e, {
                "function": "rate_recipe",
                "recipe_id": recipe_id,
                "rating": rating,
                "comment": comment
            })
            return False

    async def get_recipe(self, recipe_id: str) -> Optional[Dict]:
        """获取菜谱信息"""
        try:
            query = """
                SELECT r.*, 
                    COALESCE(AVG(rt.rating), 0) as average_rating,
                    COUNT(rt.id) as rating_count
                FROM recipes r
                LEFT JOIN ratings rt ON r.id = rt.recipe_id
                WHERE r.id = $1
                GROUP BY r.id
            """
            recipe = await self.db_service.fetch_one(query, recipe_id)
            return recipe
            
        except Exception as e:
            self.error_service.log_error(e, {
                "function": "get_recipe",
                "recipe_id": recipe_id
            })
            return None
    
    async def search_recipes(
        self,
        page: int = 1,
        per_page: int = 20,
        difficulty: Optional[str] = None,
        cooking_time: Optional[int] = None,
        cuisine_type: Optional[str] = None
    ) -> Dict:
        """搜索菜谱"""
        try:
            # 构建基础查询
            base_query = """
                FROM recipes r
                LEFT JOIN ratings rt ON r.id = rt.recipe_id
                WHERE 1=1
            """
            count_query = f"SELECT COUNT(DISTINCT r.id) {base_query}"
            
            # 添加过滤条件
            params = []
            if difficulty:
                base_query += f" AND r.difficulty = ${len(params) + 1}"
                params.append(difficulty)
            if cooking_time:
                base_query += f" AND r.cooking_time <= ${len(params) + 1}"
                params.append(cooking_time)
            if cuisine_type:
                base_query += f" AND r.cuisine_type = ${len(params) + 1}"
                params.append(cuisine_type)
            
            # 获取总数
            total = await self.db_service.fetch_val(count_query, *params)
            
            # 添加分页和排序
            query = f"""
                SELECT DISTINCT r.*,
                    COALESCE(AVG(rt.rating), 0) as average_rating
                {base_query}
                GROUP BY r.id
                ORDER BY r.created_at DESC
                LIMIT {per_page} OFFSET {(page - 1) * per_page}
            """
            
            recipes = await self.db_service.fetch(query, *params)
            
            return {
                "recipes": recipes,
                "pagination": {
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": (total + per_page - 1) // per_page
                }
            }
            
        except Exception as e:
            self.error_service.log_error(e, {
                "function": "search_recipes",
                "params": {
                    "page": page,
                    "per_page": per_page,
                    "difficulty": difficulty,
                    "cooking_time": cooking_time,
                    "cuisine_type": cuisine_type
                }
            })
            return {"recipes": [], "pagination": {
                "total": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0
            }}
    
    async def close(self):
        """关闭服务"""
        await self.db_service.close() 