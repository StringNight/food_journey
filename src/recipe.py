# src/recipe.py
from typing import List, Dict, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, Field

class Recipe:
    """菜谱类
    
    表示一个完整的菜谱，包含基本信息、食材、步骤、评分等
    支持菜谱的创建、修改、评分和营养计算
    """
    
    def __init__(
        self,
        title: str,
        ingredients: List[Dict],
        steps: List[Dict],
        author_id: str,
        difficulty: Optional[str] = None,
        cooking_time: Optional[int] = None,
        tags: Optional[List[str]] = None,
        cuisine_type: Optional[str] = None,
        servings: Optional[int] = None,
        description: Optional[str] = None
    ):
        """初始化菜谱
        
        Args:
            title: 菜谱标题
            ingredients: 食材列表，每个食材包含名称、数量和单位
            steps: 烹饪步骤列表，每个步骤包含描述和可选的图片
            author_id: 作者ID
            difficulty: 难度等级（简单/中等/困难）
            cooking_time: 烹饪时间（分钟）
            tags: 标签列表
            cuisine_type: 菜系类型
            servings: 份量（人数）
            description: 菜品描述
        """
        self.id = str(uuid.uuid4())
        self.title = title
        self.ingredients = ingredients
        self.steps = steps
        self.author_id = author_id
        self.difficulty = difficulty
        self.cooking_time = cooking_time
        self.tags = tags or []
        self.cuisine_type = cuisine_type
        self.servings = servings or 2
        self.description = description
        self.ratings = []
        self.comments = []
        self.favorites_count = 0
        self.views_count = 0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # 验证输入数据
        self._validate_ingredients()
        self._validate_steps()
    
    def _validate_ingredients(self):
        """验证食材数据的完整性和有效性
        
        Raises:
            ValueError: 当食材数据无效时抛出
        """
        required_fields = {'name', 'amount', 'unit'}
        for ingredient in self.ingredients:
            missing_fields = required_fields - set(ingredient.keys())
            if missing_fields:
                raise ValueError(f"食材缺少必要字段: {missing_fields}")
            
            if not ingredient['name'].strip():
                raise ValueError("食材名称不能为空")
            
            try:
                float(ingredient['amount'])
            except ValueError:
                raise ValueError(f"无效的食材数量: {ingredient['amount']}")
    
    def _validate_steps(self):
        """验证步骤数据的完整性和有效性
        
        Raises:
            ValueError: 当步骤数据无效时抛出
        """
        if not self.steps:
            raise ValueError("烹饪步骤不能为空")
            
        for i, step in enumerate(self.steps, 1):
            if 'description' not in step:
                raise ValueError(f"第{i}步缺少描述")
            if not step['description'].strip():
                raise ValueError(f"第{i}步描述不能为空")
            
            step['step_number'] = i
    
    def add_rating(
        self,
        user_id: str,
        rating: float,
        comment: Optional[str] = None,
        images: Optional[List[str]] = None
    ):
        """添加评分和评论
        
        Args:
            user_id: 用户ID
            rating: 评分（1-5分）
            comment: 评论内容
            images: 评论图片列表
            
        Raises:
            ValueError: 当评分无效时抛出
        """
        if not 1 <= rating <= 5:
            raise ValueError("评分必须在1-5分之间")
            
        rating_data = {
            'user_id': user_id,
            'rating': rating,
            'timestamp': datetime.now()
        }
        
        if comment:
            rating_data['comment'] = comment
            self.comments.append({
                'user_id': user_id,
                'content': comment,
                'images': images or [],
                'timestamp': datetime.now()
            })
            
        self.ratings.append(rating_data)
    
    def adjust_servings(self, new_servings: int):
        """调整份量
        
        按比例调整所有食材的用量
        
        Args:
            new_servings: 新的份量（人数）
            
        Raises:
            ValueError: 当份量无效时抛出
        """
        if new_servings < 1:
            raise ValueError("份量必须大于0")
            
        ratio = new_servings / self.servings
        for ingredient in self.ingredients:
            try:
                amount = float(ingredient['amount'])
                ingredient['amount'] = str(amount * ratio)
            except (ValueError, TypeError):
                continue
        
        self.servings = new_servings
    
    def calculate_nutrition(self, nutrition_data: Dict[str, Dict]) -> Dict[str, float]:
        """计算营养成分
        
        基于食材和用量计算总营养成分
        
        Args:
            nutrition_data: 食材营养数据库
            
        Returns:
            Dict: 营养成分计算结果
        """
        nutrition = {
            'calories': 0.0,
            'protein': 0.0,
            'fat': 0.0,
            'carbs': 0.0,
            'fiber': 0.0
        }
        
        for ingredient in self.ingredients:
            if ingredient['name'] not in nutrition_data:
                continue
                
            try:
                amount = float(ingredient['amount'])
                unit = ingredient['unit']
                item_nutrition = nutrition_data[ingredient['name']]
                
                # 转换单位并计算营养成分
                converted_amount = self._convert_unit(amount, unit, item_nutrition['base_unit'])
                for key in nutrition:
                    nutrition[key] += item_nutrition[key] * converted_amount
            except (ValueError, KeyError):
                continue
        
        return nutrition
    
    def _convert_unit(self, amount: float, from_unit: str, to_unit: str) -> float:
        """转换计量单位
        
        Args:
            amount: 数量
            from_unit: 原单位
            to_unit: 目标单位
            
        Returns:
            float: 转换后的数量
            
        Raises:
            ValueError: 当单位转换无效时抛出
        """
        # 定义常见单位转换关系
        conversions = {
            'g': {
                'kg': 0.001,
                'mg': 1000
            },
            'ml': {
                'l': 0.001,
                'dl': 0.01
            },
            'cup': {
                'ml': 250,
                'g': 250  # 对于水基础食材
            }
        }
        
        if from_unit == to_unit:
            return amount
            
        try:
            if to_unit in conversions.get(from_unit, {}):
                return amount * conversions[from_unit][to_unit]
            elif from_unit in conversions.get(to_unit, {}):
                return amount / conversions[to_unit][from_unit]
        except KeyError:
            pass
            
        raise ValueError(f"无法转换单位: {from_unit} -> {to_unit}")
    
    def estimate_cost(self, price_data: Dict[str, float]) -> float:
        """估算成本
        
        基于食材用量和单价估算总成本
        
        Args:
            price_data: 食材价格数据
            
        Returns:
            float: 估算成本
        """
        total_cost = 0.0
        
        for ingredient in self.ingredients:
            if ingredient['name'] not in price_data:
                continue
                
            try:
                amount = float(ingredient['amount'])
                unit = ingredient['unit']
                price_per_unit = price_data[ingredient['name']]
                
                # 转换单位并计算成本
                converted_amount = self._convert_unit(amount, unit, 'g')  # 假设价格基于克
                total_cost += converted_amount * price_per_unit
            except (ValueError, KeyError):
                continue
        
        return total_cost
    
    def get_preparation_steps(self) -> List[Dict]:
        """获取准备步骤
        
        将步骤分为准备和烹饪两个阶段
        
        Returns:
            List[Dict]: 准备步骤列表
        """
        prep_steps = []
        for step in self.steps:
            if any(keyword in step['description'].lower() 
                  for keyword in ['准备', '切', '洗', '泡', '腌制']):
                prep_steps.append(step)
        return prep_steps
    
    def get_cooking_steps(self) -> List[Dict]:
        """获取烹饪步骤
        
        Returns:
            List[Dict]: 烹饪步骤列表
        """
        return [step for step in self.steps 
                if step not in self.get_preparation_steps()]
    
    def to_dict(self) -> Dict:
        """转换为字典格式
        
        Returns:
            Dict: 菜谱的完整字典表示
        """
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'author_id': self.author_id,
            'ingredients': self.ingredients,
            'steps': self.steps,
            'difficulty': self.difficulty,
            'cooking_time': self.cooking_time,
            'tags': self.tags,
            'cuisine_type': self.cuisine_type,
            'servings': self.servings,
            'ratings': self.ratings,
            'comments': self.comments,
            'favorites_count': self.favorites_count,
            'views_count': self.views_count,
            'average_rating': self.average_rating,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @property
    def average_rating(self) -> float:
        """计算平均评分
        
        Returns:
            float: 平均评分，如果没有评分则返回0
        """
        if not self.ratings:
            return 0.0
        return sum(r['rating'] for r in self.ratings) / len(self.ratings)
    
    @property
    def total_time(self) -> int:
        """计算总时间
        
        包括准备时间和烹饪时间
        
        Returns:
            int: 总时间（分钟）
        """
        prep_time = sum(
            step.get('duration', 0) 
            for step in self.get_preparation_steps()
        )
        return prep_time + (self.cooking_time or 0)
    
    def increment_views(self):
        """增加浏览次数"""
        self.views_count += 1
    
    def increment_favorites(self):
        """增加收藏次数"""
        self.favorites_count += 1
    
    def decrement_favorites(self):
        """减少收藏次数"""
        if self.favorites_count > 0:
            self.favorites_count -= 1