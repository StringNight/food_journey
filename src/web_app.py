import gradio as gr
from typing import Dict, List, Optional, Tuple
import logging
from .llm_handler import LLMHandler
from .recipe_manager import RecipeManager
from .user_profile import UserProfile
import json
from datetime import datetime

class WebApp:
    """Web应用类
    
    使用Gradio构建的Web界面，提供菜谱生成、个性化推荐等功能
    """
    
    def __init__(self):
        """初始化Web应用
        
        创建必要的组件和处理器实例
        """
        self.llm = LLMHandler()
        self.recipe_manager = RecipeManager()
        self.logger = logging.getLogger(__name__)
        
        # 创建Gradio界面
        self.interface = self._build_interface()
    
    def _build_interface(self) -> gr.Blocks:
        """构建Gradio界面
        
        Returns:
            gr.Blocks: Gradio界面对象
        """
        with gr.Blocks(title="美食之旅") as interface:
            gr.Markdown("# 🍳 美食之旅")
            
            with gr.Tabs():
                # 菜谱生成标签页
                with gr.Tab("🪄 菜谱生成"):
                    self._build_recipe_generation_tab()
                
                # 个性化推荐标签页
                with gr.Tab("🎯 个性化推荐"):
                    self._build_recommendation_tab()
                
                # 用户画像标签页
                with gr.Tab("👤 用户画像"):
                    self._build_profile_tab()
                
                # 菜谱收藏标签页
                with gr.Tab("⭐ 我的收藏"):
                    self._build_favorites_tab()
            
            gr.Markdown("## 🔔 使用说明")
            gr.Markdown("""
            1. 在"菜谱生成"标签页，输入食材和偏好生成菜谱
            2. 在"个性化推荐"标签页，获取基于您口味的推荐
            3. 在"用户画像"标签页，设置您的偏好和限制
            4. 在"我的收藏"标签页，管理收藏的菜谱
            """)
        
        return interface
    
    def _build_recipe_generation_tab(self):
        """构建菜谱生成标签页"""
        with gr.Column():
            gr.Markdown("## 🪄 生成个性化菜谱")
            
            # 输入区域
            ingredients = gr.Textbox(
                label="可用食材（用逗号分隔）",
                placeholder="例如：鸡胸肉, 西兰花, 胡萝卜"
            )
            
            with gr.Row():
                cooking_time = gr.Slider(
                    minimum=5,
                    maximum=120,
                    value=30,
                    step=5,
                    label="期望烹饪时间（分钟）"
                )
                
                difficulty = gr.Dropdown(
                    choices=["简单", "中等", "困难"],
                    value="简单",
                    label="期望难度"
                )
            
            dietary_restrictions = gr.CheckboxGroup(
                choices=["无麸质", "素食", "低脂", "低碳水"],
                label="饮食限制"
            )
            
            # 生成按钮
            generate_btn = gr.Button("生成菜谱", variant="primary")
            
            # 输出区域
            with gr.Column():
                recipe_output = gr.Markdown(label="生成的菜谱")
                nutrition_info = gr.JSON(label="营养信息")
                cooking_tips = gr.Markdown(label="烹饪技巧")
            
            # 绑定事件
            generate_btn.click(
                fn=self._generate_recipe,
                inputs=[ingredients, cooking_time, difficulty, dietary_restrictions],
                outputs=[recipe_output, nutrition_info, cooking_tips]
            )
    
    def _build_recommendation_tab(self):
        """构建个性化推荐标签页"""
        with gr.Column():
            gr.Markdown("## 🎯 为您推荐")
            
            # 推荐选项
            with gr.Row():
                cuisine_type = gr.Dropdown(
                    choices=["全部", "中餐", "西餐", "日料", "韩餐"],
                    value="全部",
                    label="菜系"
                )
                
                meal_type = gr.Dropdown(
                    choices=["全部", "早餐", "午餐", "晚餐", "小食"],
                    value="全部",
                    label="餐点类型"
                )
            
            # 推荐按钮
            refresh_btn = gr.Button("刷新推荐", variant="primary")
            
            # 推荐结果
            recommendations = gr.Gallery(label="推荐菜谱")
            recipe_details = gr.Markdown(label="菜谱详情")
            
            # 绑定事件
            refresh_btn.click(
                fn=self._get_recommendations,
                inputs=[cuisine_type, meal_type],
                outputs=[recommendations, recipe_details]
            )
    
    def _build_profile_tab(self):
        """构建用户画像标签页"""
        with gr.Column():
            gr.Markdown("## 👤 个性化设置")
            
            # 基本信息
            with gr.Row():
                cooking_skill = gr.Radio(
                    choices=["初学者", "进阶", "专业"],
                    value="初学者",
                    label="烹饪技能"
                )
                
                preferred_cuisine = gr.CheckboxGroup(
                    choices=["中餐", "西餐", "日料", "韩餐", "其他"],
                    label="偏好菜系"
                )
            
            # 饮食偏好
            with gr.Column():
                allergies = gr.Textbox(
                    label="过敏源（用逗号分隔）",
                    placeholder="例如：花生, 海鲜, 乳制品"
                )
                
                health_goals = gr.CheckboxGroup(
                    choices=["减重", "增肌", "营养均衡", "素食"],
                    label="健康目标"
                )
            
            # 保存按钮
            save_btn = gr.Button("保存设置", variant="primary")
            
            # 保存结果
            save_result = gr.Markdown()
            
            # 绑定事件
            save_btn.click(
                fn=self._save_profile,
                inputs=[cooking_skill, preferred_cuisine, allergies, health_goals],
                outputs=[save_result]
            )
    
    def _build_favorites_tab(self):
        """构建收藏标签页"""
        with gr.Column():
            gr.Markdown("## ⭐ 收藏的菜谱")
            
            # 收藏列表
            favorites = gr.Gallery(label="收藏列表")
            
            with gr.Row():
                remove_btn = gr.Button("取消收藏")
                view_btn = gr.Button("查看详情")
            
            recipe_details = gr.Markdown(label="菜谱详情")
            
            # 绑定事件
            view_btn.click(
                fn=self._view_favorite,
                inputs=[favorites],
                outputs=[recipe_details]
            )
            
            remove_btn.click(
                fn=self._remove_favorite,
                inputs=[favorites],
                outputs=[favorites, recipe_details]
            )
    
    async def _generate_recipe(
        self,
        ingredients: str,
        cooking_time: int,
        difficulty: str,
        dietary_restrictions: List[str]
    ) -> Tuple[str, Dict, str]:
        """生成菜谱
        
        Args:
            ingredients: 食材列表
            cooking_time: 烹饪时间
            difficulty: 难度等级
            dietary_restrictions: 饮食限制
            
        Returns:
            Tuple: (菜谱文本, 营养信息, 烹饪技巧)
        """
        try:
            # 解析食材列表
            ingredient_list = [i.strip() for i in ingredients.split(",") if i.strip()]
            
            # 构建偏好数据
            preferences = {
                "cooking_time": cooking_time,
                "difficulty": difficulty,
                "dietary_restrictions": dietary_restrictions
            }
            
            # 生成菜谱
            recipe = await self.llm.generate_recipe(ingredient_list, preferences)
            
            # 获取营养信息
            nutrition = await self.llm.get_nutrition_analysis(recipe["ingredients"])
            
            # 获取烹饪技巧
            tips = await self.llm.get_cooking_tips(json.dumps(recipe, ensure_ascii=False))
            
            return (
                self._format_recipe(recipe),
                nutrition,
                "\n".join(tips)
            )
            
        except Exception as e:
            self.logger.error(f"生成菜谱失败: {e}")
            return (
                "生成失败，请稍后重试",
                {},
                ""
            )
    
    async def _get_recommendations(
        self,
        cuisine_type: str,
        meal_type: str
    ) -> Tuple[List[str], str]:
        """获取推荐菜谱
        
        Args:
            cuisine_type: 菜系类型
            meal_type: 餐点类型
            
        Returns:
            Tuple: (推荐图片列表, 详情文本)
        """
        try:
            # TODO: 实现推荐逻辑
            return [], "暂无推荐"
        except Exception as e:
            self.logger.error(f"获取推荐失败: {e}")
            return [], "获取推荐失败，请稍后重试"
    
    def _save_profile(
        self,
        cooking_skill: str,
        preferred_cuisine: List[str],
        allergies: str,
        health_goals: List[str]
    ) -> str:
        """保存用户画像
        
        Args:
            cooking_skill: 烹饪技能
            preferred_cuisine: 偏好菜系
            allergies: 过敏源
            health_goals: 健康目标
            
        Returns:
            str: 保存结果消息
        """
        try:
            # TODO: 实现保存逻辑
            return "设置已保存"
        except Exception as e:
            self.logger.error(f"保存设置失败: {e}")
            return "保存失败，请稍后重试"
    
    def _view_favorite(self, selected: str) -> str:
        """查看收藏的菜谱
        
        Args:
            selected: 选中的菜谱ID
            
        Returns:
            str: 菜谱详情
        """
        try:
            # TODO: 实现查看逻辑
            return "暂无详情"
        except Exception as e:
            self.logger.error(f"查看收藏失败: {e}")
            return "获取详情失败，请稍后重试"
    
    def _remove_favorite(
        self,
        selected: str
    ) -> Tuple[List[str], str]:
        """取消收藏
        
        Args:
            selected: 选中的菜谱ID
            
        Returns:
            Tuple: (更新后的收藏列表, 结果消息)
        """
        try:
            # TODO: 实现取消收藏逻辑
            return [], "已取消收藏"
        except Exception as e:
            self.logger.error(f"取消收藏失败: {e}")
            return [], "操作失败，请稍后重试"
    
    def _format_recipe(self, recipe: Dict) -> str:
        """格式化菜谱文本
        
        Args:
            recipe: 菜谱数据
            
        Returns:
            str: 格式化后的菜谱文本
        """
        return f"""
        # {recipe['title']}
        
        ## 食材
        {self._format_ingredients(recipe['ingredients'])}
        
        ## 步骤
        {self._format_steps(recipe['steps'])}
        
        ## 小贴士
        - 烹饪时间：{recipe.get('cooking_time', '未指定')}分钟
        - 难度：{recipe.get('difficulty', '未指定')}
        """
    
    def _format_ingredients(self, ingredients: List[Dict]) -> str:
        """格式化食材列表
        
        Args:
            ingredients: 食材数据
            
        Returns:
            str: 格式化后的食材文本
        """
        return "\n".join([
            f"- {item['name']}: {item['amount']} {item.get('unit', '')}"
            for item in ingredients
        ])
    
    def _format_steps(self, steps: List[Dict]) -> str:
        """格式化步骤列表
        
        Args:
            steps: 步骤数据
            
        Returns:
            str: 格式化后的步骤文本
        """
        return "\n".join([
            f"{i+1}. {step['description']}"
            for i, step in enumerate(steps)
        ])
    
    def launch(self, **kwargs):
        """启动Web应用
        
        Args:
            **kwargs: 传递给Gradio launch的参数
        """
        self.interface.launch(**kwargs) 