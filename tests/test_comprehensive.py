"""综合测试模块

测试前端和后端的主要功能集成
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
from datetime import datetime, timedelta

# 设置日志
logger = logging.getLogger(__name__)

# 标记所有测试为异步
pytestmark = pytest.mark.asyncio

# 测试数据
TEST_USER_DATA = {
    "username": "testuser",
    "password": "Test@123456"
}

# 测试用例序列
async def test_end_to_end_workflow(test_client: AsyncClient):
    """测试完整的端到端流程，包括用户注册、登录、创建和管理食谱等"""
    
    # 1. 注册用户
    user_token = await register_and_login(test_client)
    assert user_token, "用户注册登录失败"
    
    # 2. 更新用户档案
    profile_updated = await update_user_profile(test_client, user_token)
    assert profile_updated, "更新用户档案失败"
    
    # 3. 创建食谱
    recipe_id = await create_recipe(test_client, user_token)
    assert recipe_id, "创建食谱失败"
    
    # 4. 获取食谱详情
    recipe = await get_recipe(test_client, recipe_id)
    assert recipe, "获取食谱详情失败"
    
    # 5. 搜索食谱
    search_results = await search_recipes(test_client)
    assert search_results, "搜索食谱失败"
    
    # 6. 为食谱评分
    rated = await rate_recipe(test_client, user_token, recipe_id)
    assert rated, "为食谱评分失败"
    
    # 7. 收藏食谱
    favorite_added = await add_to_favorites(test_client, user_token, recipe_id)
    assert favorite_added, "收藏食谱失败"
    
    # 8. 获取收藏列表
    favorites = await get_favorites(test_client, user_token)
    assert favorites, "获取收藏列表失败"
    
    # 9. 记录一次锻炼
    workout_id = await record_workout(test_client, user_token)
    assert workout_id, "记录锻炼失败"
    
    # 10. 获取锻炼记录
    workouts = await get_workouts(test_client, user_token)
    assert workouts, "获取锻炼记录失败"
    
    # 11. 更新食谱
    updated = await update_recipe(test_client, user_token, recipe_id)
    assert updated, "更新食谱失败"
    
    # 12. 测试AI聊天功能
    chat_response = await test_chat(test_client, user_token)
    assert chat_response, "AI聊天功能测试失败"

# 辅助函数
async def register_and_login(client: AsyncClient) -> str:
    """注册并登录用户，返回访问令牌"""
    try:
        # 注册
        register_response = await client.post(
            "/api/v1/auth/register", 
            json=TEST_USER_DATA
        )
        
        if register_response.status_code == 409:
            # 用户已存在，直接登录
            login_response = await client.post(
                "/api/v1/auth/login/json", 
                json=TEST_USER_DATA
            )
            
            assert login_response.status_code == 200, f"登录失败: {login_response.text}"
            return login_response.json()["token"]["access_token"]
        
        assert register_response.status_code == 201, f"注册失败: {register_response.text}"
        
        # 登录以获取令牌
        login_response = await client.post(
            "/api/v1/auth/login/json", 
            json=TEST_USER_DATA
        )
        
        assert login_response.status_code == 200, f"登录失败: {login_response.text}"
        return login_response.json()["token"]["access_token"]
    
    except Exception as e:
        logger.error(f"注册登录异常: {str(e)}")
        return None

async def update_user_profile(client: AsyncClient, token: str) -> bool:
    """更新用户档案"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. 更新基本信息
        basic_profile_data = {
            "birth_date": "1990-01-01",
            "gender": "男",
            "height": 175.0,
            "weight": 70.0,
            "body_fat_percentage": 18.0,
            "health_conditions": ["无"]
        }
        
        response = await client.put(
            "/api/v1/profile/basic",
            json=basic_profile_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"更新用户基本信息失败: {response.text}"
        
        # 2. 更新饮食偏好
        diet_profile_data = {
            "health_goals": ["保持健康", "增肌"],
            "cooking_skill_level": "中级",
            "favorite_cuisines": ["中餐", "意大利菜"],
            "dietary_restrictions": ["无"],
            "allergies": ["无"],
            "nutrition_goals": {
                "protein": 150,
                "carbs": 250,
                "fat": 70
            }
        }
        
        response = await client.put(
            "/api/v1/profile/diet",
            json=diet_profile_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"更新用户饮食偏好失败: {response.text}"
        
        # 3. 更新健身偏好
        fitness_profile_data = {
            "fitness_level": "中级",
            "exercise_frequency": 4,
            "preferred_exercises": ["跑步", "力量训练"],
            "fitness_goals": ["增肌", "提高耐力"]
        }
        
        response = await client.put(
            "/api/v1/profile/fitness",
            json=fitness_profile_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"更新用户健身偏好失败: {response.text}"
        
        return True
    
    except Exception as e:
        logger.error(f"更新用户档案异常: {str(e)}")
        return False

async def create_recipe(client: AsyncClient, token: str) -> str:
    """创建食谱并返回食谱ID"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        recipe_data = {
            "title": "测试食谱",
            "description": "这是一个用于测试的食谱",
            "ingredients": [
                {"name": "西红柿", "amount": "2个"},
                {"name": "鸡蛋", "amount": "3个"},
                {"name": "食用油", "amount": "适量"},
                {"name": "盐", "amount": "适量"}
            ],
            "steps": [
                {"step": "1", "description": "西红柿洗净切块"},
                {"step": "2", "description": "锅中放油，放入西红柿炒软"},
                {"step": "3", "description": "打入鸡蛋，翻炒均匀"},
                {"step": "4", "description": "加入适量盐调味即可"}
            ],
            "cooking_time": 15,
            "difficulty": "简单",
            "cuisine_type": "中餐"
        }
        
        response = await client.post(
            "/api/v1/recipes/create_recipe",
            json=recipe_data,
            headers=headers
        )
        
        assert response.status_code == 201, f"创建食谱失败: {response.text}"
        return response.json()["recipe"]["id"]
    
    except Exception as e:
        logger.error(f"创建食谱异常: {str(e)}")
        return None

async def get_recipe(client: AsyncClient, recipe_id: str) -> Dict:
    """获取食谱详情"""
    try:
        response = await client.get(f"/api/v1/recipes/{recipe_id}")
        
        assert response.status_code == 200, f"获取食谱失败: {response.text}"
        return response.json()["recipe"]
    
    except Exception as e:
        logger.error(f"获取食谱异常: {str(e)}")
        return None

async def search_recipes(client: AsyncClient) -> List[Dict]:
    """搜索食谱"""
    try:
        response = await client.get(
            "/api/v1/recipes/",
            params={"keyword": "测试", "page": 1, "per_page": 10}
        )
        
        assert response.status_code == 200, f"搜索食谱失败: {response.text}"
        return response.json()["recipes"]
    
    except Exception as e:
        logger.error(f"搜索食谱异常: {str(e)}")
        return None

async def rate_recipe(client: AsyncClient, token: str, recipe_id: str) -> bool:
    """为食谱评分"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        rating_data = {
            "rating": 5,
            "comment": "很棒的食谱，简单易做又美味！"
        }
        
        response = await client.post(
            f"/api/v1/recipes/{recipe_id}/rate",
            json=rating_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"评分失败: {response.text}"
        return True
    
    except Exception as e:
        logger.error(f"评分异常: {str(e)}")
        return False

async def add_to_favorites(client: AsyncClient, token: str, recipe_id: str) -> bool:
    """将食谱添加到收藏"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.post(
            f"/api/v1/favorites/{recipe_id}",
            headers=headers
        )
        
        assert response.status_code == 201, f"添加收藏失败: {response.text}"
        return True
    
    except Exception as e:
        logger.error(f"添加收藏异常: {str(e)}")
        return False

async def get_favorites(client: AsyncClient, token: str) -> List[Dict]:
    """获取收藏列表"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.get(
            "/api/v1/favorites",
            headers=headers
        )
        
        # 接受200或307状态码
        assert response.status_code in [200, 307], f"获取收藏列表失败: {response.text}"
        
        # 如果是307重定向，手动跟随重定向
        if response.status_code == 307:
            redirect_url = response.headers.get("location")
            if redirect_url:
                response = await client.get(
                    redirect_url,
                    headers=headers
                )
                assert response.status_code == 200, f"重定向后获取收藏列表失败: {response.text}"
        
        return response.json()["favorites"]
    
    except Exception as e:
        logger.error(f"获取收藏列表异常: {str(e)}")
        return None

async def record_workout(client: AsyncClient, token: str) -> str:
    """记录锻炼"""
    try:
        logger.info("开始记录锻炼")
        headers = {"Authorization": f"Bearer {token}"}
        
        # 使用当前日期的前一天以确保不会被视为未来日期
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        workout_data = {
            "name": "胸部和背部训练",
            "notes": "感觉不错，能量充沛",
            "duration": 45,
            "workout_date": yesterday,
            "exercises": [
                {
                    "exercise_type": "STRENGTH",
                    "exercise_name": "卧推",
                    "sets": 3,
                    "reps": 12,
                    "weight": 60
                },
                {
                    "exercise_type": "STRENGTH",
                    "exercise_name": "引体向上",
                    "sets": 4,
                    "reps": 8,
                    "weight": 0
                }
            ]
        }
        
        response = await client.post(
            "/api/v1/workouts",
            json=workout_data,
            headers=headers
        )
        
        assert response.status_code == 201, f"记录锻炼失败: {response.text}"
        response_data = response.json()
        # 从响应中提取workout对象的id
        workout_id = response_data["workout"]["id"]
        logger.info(f"成功记录锻炼，ID: {workout_id}")
        return workout_id
    
    except Exception as e:
        logger.error(f"记录锻炼异常: {str(e)}")
        return None

async def get_workouts(client: AsyncClient, token: str) -> List[Dict]:
    """获取锻炼记录"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.get(
            "/api/v1/workouts",
            headers=headers
        )
        
        assert response.status_code == 200, f"获取锻炼记录失败: {response.text}"
        return response.json()["workouts"]
    
    except Exception as e:
        logger.error(f"获取锻炼记录异常: {str(e)}")
        return None

async def update_recipe(client: AsyncClient, token: str, recipe_id: str) -> bool:
    """更新食谱"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        update_data = {
            "title": "更新后的测试食谱",
            "description": "这是一个已更新的测试食谱描述",
            "cooking_time": 20
        }
        
        response = await client.put(
            f"/api/v1/recipes/{recipe_id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"更新食谱失败: {response.text}"
        return True
    
    except Exception as e:
        logger.error(f"更新食谱异常: {str(e)}")
        return False

async def test_chat(test_client: AsyncClient, test_user_token: str) -> Dict:
    """测试AI聊天功能"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}

        chat_data = {
            "message": "请给我推荐一道适合初学者的菜谱",
            "model": "qwen2.5:14b",
            "max_tokens": 500
        }

        response = await test_client.post(
            "/api/v1/chat/stream",
            json=chat_data,
            headers=headers
        )

        assert response.status_code == 200, f"聊天功能测试失败: {response.text}"
        return {"success": True}

    except Exception as e:
        logger.error(f"聊天功能测试异常: {str(e)}")
        return None 