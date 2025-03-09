"""前后端集成测试模块

测试前端与后端的API集成
"""

import pytest
import logging
import uuid
import os
import json
from httpx import AsyncClient
from fastapi import status
import asyncio
from typing import Dict, List, Any

# 设置日志
logger = logging.getLogger(__name__)

# 标记所有测试为异步
pytestmark = pytest.mark.asyncio

# 测试用例：食谱相关功能集成测试
class TestRecipeIntegration:
    """测试前端与后端食谱相关功能的集成"""
    
    async def test_recipe_listing_and_details(self, test_client: AsyncClient, test_user_token: str):
        """测试食谱列表和详情功能"""
        
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 1. 创建食谱
        recipe_data = {
            "title": "前后端集成测试食谱",
            "description": "这是一个用于测试前后端集成的食谱",
            "ingredients": [
                {"name": "牛肉", "amount": "300克"},
                {"name": "胡萝卜", "amount": "1根"},
                {"name": "土豆", "amount": "2个"},
                {"name": "调料", "amount": "适量"}
            ],
            "steps": [
                {"step": "1", "description": "牛肉切块焯水"},
                {"step": "2", "description": "胡萝卜和土豆切块"},
                {"step": "3", "description": "锅中加油，放入牛肉煸炒"},
                {"step": "4", "description": "加入胡萝卜和土豆，加水炖煮至软烂"}
            ],
            "cooking_time": 45,
            "difficulty": "中等",
            "cuisine_type": "中餐"
        }
        
        response = await test_client.post(
            "/api/v1/recipes/create_recipe",
            json=recipe_data,
            headers=headers
        )
        
        assert response.status_code == 201, f"创建食谱失败: {response.text}"
        recipe_id = response.json()["recipe"]["id"]
        
        # 2. 获取食谱列表
        response = await test_client.get(
            "/api/v1/recipes/",
            params={"page": 1, "per_page": 10}
        )
        
        assert response.status_code == 200, f"获取食谱列表失败: {response.text}"
        recipes = response.json()["recipes"]
        assert isinstance(recipes, list), "响应应该包含食谱列表"
        
        # 3. 搜索食谱
        response = await test_client.get(
            "/api/v1/recipes/",
            params={"keyword": "集成测试", "page": 1, "per_page": 10}
        )
        
        assert response.status_code == 200, f"搜索食谱失败: {response.text}"
        search_results = response.json()["recipes"]
        assert any("集成测试" in recipe["title"] for recipe in search_results), "搜索结果应该包含关键词匹配的食谱"
        
        # 4. 获取食谱详情
        response = await test_client.get(
            f"/api/v1/recipes/{recipe_id}",
            headers=headers
        )
        
        assert response.status_code == 200, f"获取食谱详情失败: {response.text}"
        recipe = response.json()["recipe"]
        assert recipe["id"] == recipe_id, "返回的食谱ID应该与请求的ID匹配"
        assert recipe["title"] == recipe_data["title"], "返回的食谱标题应该与创建时一致"
    
    async def test_recipe_rating_and_favorites(self, test_client: AsyncClient, test_user_token: str):
        """测试食谱评分和收藏功能"""
        
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 1. 创建食谱
        recipe_data = {
            "title": "评分与收藏测试食谱",
            "description": "这是一个用于测试评分与收藏功能的食谱",
            "ingredients": [
                {"name": "鸡胸肉", "amount": "200克"},
                {"name": "西兰花", "amount": "100克"},
                {"name": "橄榄油", "amount": "10毫升"}
            ],
            "steps": [
                {"step": "1", "description": "鸡胸肉切丁"},
                {"step": "2", "description": "西兰花切小朵焯水"},
                {"step": "3", "description": "锅中加热橄榄油，放入鸡胸肉翻炒"},
                {"step": "4", "description": "加入西兰花一起翻炒"}
            ],
            "cooking_time": 20,
            "difficulty": "简单",
            "cuisine_type": "西餐"
        }
        
        response = await test_client.post(
            "/api/v1/recipes/create_recipe",
            json=recipe_data,
            headers=headers
        )
        
        assert response.status_code == 201, f"创建食谱失败: {response.text}"
        recipe_id = response.json()["recipe"]["id"]
        
        # 2. 为食谱评分
        rating_data = {
            "rating": 4.5,
            "comment": "很好吃，下次还会做"
        }
        
        response = await test_client.post(
            f"/api/v1/recipes/{recipe_id}/rate",
            json=rating_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"评分失败: {response.text}"
        
        # 3. 添加到收藏
        response = await test_client.post(
            f"/api/v1/favorites/{recipe_id}",
            headers=headers
        )
        
        assert response.status_code == 201, f"添加收藏失败: {response.text}"
        
        # 4. 获取收藏列表
        response = await test_client.get(
            "/api/v1/favorites/",
            headers=headers
        )
        
        assert response.status_code == 200, f"获取收藏列表失败: {response.text}"
        favorites = response.json()["favorites"]
        assert any(favorite["id"] == recipe_id for favorite in favorites), "收藏列表应该包含新收藏的食谱"

# 测试用例：用户档案功能集成测试
class TestUserProfileIntegration:
    """测试前端与后端用户档案相关功能的集成"""
    
    async def test_profile_update_and_retrieval(self, test_client: AsyncClient, test_user_token: str):
        """测试用户档案更新和获取功能"""
        
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 1. 更新用户基本信息
        basic_profile_data = {
            "birth_date": "1992-05-15",
            "gender": "女",
            "height": 165.0,
            "weight": 58.0,
            "body_fat_percentage": 22.0,
            "health_conditions": ["无"]
        }
        
        response = await test_client.put(
            "/api/v1/profile/basic",
            json=basic_profile_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"更新用户基本信息失败: {response.text}"
        
        # 2. 更新用户饮食偏好
        diet_profile_data = {
            "health_goals": ["减脂", "增强体质"],
            "cooking_skill_level": "初级",
            "favorite_cuisines": ["日料", "韩餐"],
            "dietary_restrictions": ["低碳水"],
            "allergies": ["乳制品"],
            "nutrition_goals": {
                "protein": 120,
                "carbs": 150,
                "fat": 60
            }
        }
        
        response = await test_client.put(
            "/api/v1/profile/diet",
            json=diet_profile_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"更新用户饮食偏好失败: {response.text}"
        
        # 3. 更新用户健身偏好
        fitness_profile_data = {
            "fitness_level": "初级",
            "exercise_frequency": 3,
            "preferred_exercises": ["瑜伽", "游泳"],
            "fitness_goals": ["减重", "提高柔韧性"]
        }
        
        response = await test_client.put(
            "/api/v1/profile/fitness",
            json=fitness_profile_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"更新用户健身偏好失败: {response.text}"
    
        # 4. 获取完整用户档案
        response = await test_client.get(
            "/api/v1/profile",
            headers=headers
        )
    
        assert response.status_code == 200, f"获取用户档案失败: {response.text}"
        user_profile = response.json()
    
        # 5. 验证更新是否生效
        assert user_profile["health_profile"]["height"] == 165.0
        assert user_profile["health_profile"]["weight"] == 58.0
        assert user_profile["diet_profile"]["cooking_skill_level"] == "初级"
        assert "日料" in user_profile["diet_profile"]["favorite_cuisines"]
        assert user_profile["fitness_profile"]["fitness_level"] == "初级"
        assert "瑜伽" in user_profile["fitness_profile"]["preferred_exercises"]

# 测试用例：锻炼记录功能集成测试
class TestWorkoutIntegration:
    """测试前端与后端锻炼记录相关功能的集成"""
    
    async def test_workout_record_and_history(self, test_client: AsyncClient, test_user_token: str):
        """测试锻炼记录的创建和查询功能"""
    
        headers = {"Authorization": f"Bearer {test_user_token}"}
    
        # 1. 记录锻炼
        workout_data = {
            "name": "有氧和力量复合训练",
            "workout_date": "2023-12-15T00:00:00Z",
            "duration": 60,
            "notes": "感觉今天状态很好，完成了预定的训练计划",
            "exercises": [
                {
                    "exercise_type": "CARDIO",
                    "exercise_name": "慢跑",
                    "sets": 1,
                    "reps": 1,
                    "duration": 30,
                    "distance": 5,
                    "notes": "保持匀速"
                },
                {
                    "exercise_type": "STRENGTH",
                    "exercise_name": "高强度间歇训练",
                    "sets": 5,
                    "reps": 4,
                    "duration": 20,
                    "notes": "每组间隔30秒休息"
                }
            ]
        }
    
        response = await test_client.post(
            "/api/v1/workouts",
            json=workout_data,
            headers=headers
        )
    
        assert response.status_code == 201, f"记录锻炼失败: {response.text}"
        workout_id = response.json()["workout"]["id"]
    
        # 2. 查询锻炼历史
        response = await test_client.get(
            "/api/v1/workouts",
            headers=headers
        )
    
        assert response.status_code == 200, f"查询锻炼历史失败: {response.text}"
        workouts = response.json()["workouts"]
        assert len(workouts) > 0, "应该有至少一条锻炼记录"
    
        # 3. 获取单个锻炼详情
        response = await test_client.get(
            f"/api/v1/workouts/{workout_id}",
            headers=headers
        )
    
        assert response.status_code == 200, f"获取锻炼详情失败: {response.text}"
        workout = response.json()["workout"]
        assert workout["name"] == workout_data["name"], "锻炼名称应该与创建时一致"
        assert len(workout["exercises"]) == len(workout_data["exercises"]), "锻炼项目数量应该与创建时一致"

# 测试用例：AI聊天功能集成测试
class TestChatIntegration:
    """测试前端与后端AI聊天功能的集成"""
    
    async def test_text_chat(self, test_client: AsyncClient, test_user_token: str, mock_ai_service):
        """测试文本聊天功能"""
    
        headers = {"Authorization": f"Bearer {test_user_token}"}
    
        chat_data = {
            "message": "请推荐一个健康的晚餐食谱",
            "model": "qwen2.5:14b",
            "max_tokens": 500
        }
    
        response = await test_client.post(
            "/api/v1/chat/stream",
            json=chat_data,
            headers=headers
        )
    
        assert response.status_code == 200, f"发送聊天消息失败: {response.text}"
        
    async def test_chat_message_history(self, test_client: AsyncClient, test_user_token: str):
        """测试聊天历史记录功能"""
    
        headers = {"Authorization": f"Bearer {test_user_token}"}
    
        # 1. 发送聊天消息
        chat_data = {
            "message": "你好，我想学做菜",
            "model": "qwen2.5:14b",
            "max_tokens": 500,
            "save_history": True
        }
    
        response = await test_client.post(
            "/api/v1/chat/stream",
            json=chat_data,
            headers=headers
        )
    
        assert response.status_code == 200, f"发送聊天消息失败: {response.text}"
    
        # 2. 获取聊天历史
        response = await test_client.get(
            "/api/v1/chat/history?page=1&per_page=10",
            headers=headers
        )
    
        assert response.status_code == 200, f"获取聊天历史失败: {response.text}"
        history = response.json()
        assert len(history["messages"]) > 0, "应该有聊天历史记录" 