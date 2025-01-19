"""菜谱相关功能的测试模块"""

import pytest
from httpx import AsyncClient
import logging
import asyncio
from datetime import datetime

# 设置日志
logger = logging.getLogger(__name__)

# 标记所有测试为异步
pytestmark = pytest.mark.asyncio

async def test_create_recipe(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试创建菜谱功能"""
    try:
        # 设置认证头
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 发送创建菜谱请求
        logger.info("开始创建菜谱测试")
        response = await test_client.post(
            "/api/v1/recipes/",
            json=test_recipe_data,
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 201, f"创建菜谱失败: {response.text}"
        data = response.json()
        
        # 验证返回的数据
        assert data["schema_version"] == "1.0"
        recipe = data["recipe"]
        assert recipe["title"] == test_recipe_data["title"]
        assert recipe["description"] == test_recipe_data["description"]
        assert recipe["ingredients"] == test_recipe_data["ingredients"]
        assert recipe["steps"] == test_recipe_data["steps"]
        assert recipe["cooking_time"] == test_recipe_data["cooking_time"]
        assert recipe["difficulty"] == test_recipe_data["difficulty"]
        assert recipe["cuisine_type"] == test_recipe_data["cuisine_type"]
        assert "id" in recipe
        assert "created_at" in recipe
        assert "updated_at" in recipe
        assert "author_id" in recipe
        
        logger.info(f"菜谱创建成功，ID: {recipe['id']}")
        
    except AssertionError as e:
        logger.error(f"测试断言失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        raise

async def test_get_recipe(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试获取菜谱功能"""
    try:
        # 首先创建一个菜谱
        headers = {"Authorization": f"Bearer {test_user_token}"}
        create_response = await test_client.post(
            "/api/v1/recipes/",
            json=test_recipe_data,
            headers=headers,
            timeout=10.0
        )
        assert create_response.status_code == 201
        recipe_id = create_response.json()["recipe"]["id"]
        
        # 获取创建的菜谱
        logger.info(f"Attempting to get recipe with id: {recipe_id}")
        response = await test_client.get(
            f"/api/v1/recipes/{recipe_id}",
            headers=headers,
            timeout=10.0
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        
        # 验证返回的数据
        assert data["schema_version"] == "1.0"
        recipe = data["recipe"]
        assert recipe["id"] == recipe_id
        assert recipe["title"] == test_recipe_data["title"]
        assert recipe["description"] == test_recipe_data["description"]
        
        logger.info("Recipe retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error in test_get_recipe: {e}")
        raise

async def test_search_recipes(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试搜索菜谱功能"""
    try:
        # 创建测试菜谱
        headers = {"Authorization": f"Bearer {test_user_token}"}
        await test_client.post(
            "/api/v1/recipes/",
            json=test_recipe_data,
            headers=headers,
            timeout=10.0
        )
        
        # 搜索菜谱
        logger.info("Attempting to search recipes")
        response = await test_client.get(
            "/api/v1/recipes/",
            params={"keyword": test_recipe_data["title"]},
            headers=headers,
            timeout=10.0
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["schema_version"] == "1.0"
        recipes = data["recipes"]
        assert len(recipes) > 0
        assert recipes[0]["title"] == test_recipe_data["title"]
        
        logger.info("Recipe search completed successfully")
        
    except Exception as e:
        logger.error(f"Error in test_search_recipes: {e}")
        raise

async def test_rate_recipe(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试菜谱评分功能"""
    try:
        # 创建测试菜谱
        headers = {"Authorization": f"Bearer {test_user_token}"}
        create_response = await test_client.post(
            "/api/v1/recipes/",
            json=test_recipe_data,
            headers=headers,
            timeout=10.0
        )
        recipe_id = create_response.json()["recipe"]["id"]
        
        # 评分数据
        rating_data = {
            "rating": 4.5,
            "comment": "这是一个测试评论"
        }
        
        # 提交评分
        logger.info(f"Attempting to rate recipe with id: {recipe_id}")
        response = await test_client.post(
            f"/api/v1/recipes/{recipe_id}/rate",
            json=rating_data,
            headers=headers,
            timeout=10.0
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["schema_version"] == "1.0"
        recipe = data["recipe"]
        assert recipe["id"] == recipe_id
        assert recipe["average_rating"] == rating_data["rating"]
        
        logger.info("Recipe rating submitted successfully")
        
    except Exception as e:
        logger.error(f"Error in test_rate_recipe: {e}")
        raise

async def test_invalid_recipe_data(test_client: AsyncClient, test_user_token: str):
    """测试无效的菜谱数据处理"""
    try:
        # 准备无效的菜谱数据
        invalid_recipe_data = {
            "title": "",  # 空标题
            "description": "测试描述",
            "ingredients": [],  # 空食材列表
            "steps": []  # 空步骤列表
        }
        
        # 设置认证头
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 尝试创建无效菜谱
        logger.info("Attempting to create recipe with invalid data")
        response = await test_client.post(
            "/api/v1/recipes/",
            json=invalid_recipe_data,
            headers=headers,
            timeout=10.0
        )
        
        # 验证响应
        assert response.status_code == 422  # 验证错误
        
        logger.info("Invalid recipe data handled correctly")
        
    except Exception as e:
        logger.error(f"Error in test_invalid_recipe_data: {e}")
        raise

async def test_unauthorized_access(test_client: AsyncClient, test_recipe_data: dict):
    """测试未授权访问处理"""
    try:
        # 尝试在没有认证的情况下创建菜谱
        logger.info("Attempting to create recipe without authentication")
        response = await test_client.post(
            "/api/v1/recipes/",
            json=test_recipe_data,
            timeout=10.0
        )
        
        # 验证响应
        assert response.status_code == 401  # 未授权
        
        logger.info("Unauthorized access handled correctly")
        
    except Exception as e:
        logger.error(f"Error in test_unauthorized_access: {e}")
        raise

async def test_update_recipe(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试更新菜谱功能"""
    try:
        # 首先创建一个菜谱
        headers = {"Authorization": f"Bearer {test_user_token}"}
        create_response = await test_client.post(
            "/api/v1/recipes/",
            json=test_recipe_data,
            headers=headers
        )
        recipe_id = create_response.json()["recipe"]["id"]
        
        # 更新数据
        update_data = {
            "title": "更新后的菜谱",
            "description": "更新后的描述",
            "cooking_time": 45
        }
        
        # 发送更新请求
        logger.info(f"Attempting to update recipe with id: {recipe_id}")
        response = await test_client.put(
            f"/api/v1/recipes/{recipe_id}",
            json=update_data,
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        recipe = data["recipe"]
        assert recipe["title"] == update_data["title"]
        assert recipe["description"] == update_data["description"]
        assert recipe["cooking_time"] == update_data["cooking_time"]
        
        logger.info("Recipe updated successfully")
        
    except Exception as e:
        logger.error(f"Error in test_update_recipe: {e}")
        raise

async def test_delete_recipe(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试删除菜谱功能"""
    try:
        # 首先创建一个菜谱
        headers = {"Authorization": f"Bearer {test_user_token}"}
        create_response = await test_client.post(
            "/api/v1/recipes/",
            json=test_recipe_data,
            headers=headers
        )
        recipe_id = create_response.json()["recipe"]["id"]
        
        # 删除菜谱
        logger.info(f"Attempting to delete recipe with id: {recipe_id}")
        response = await test_client.delete(
            f"/api/v1/recipes/{recipe_id}",
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 204
        
        # 验证菜谱已被删除
        get_response = await test_client.get(
            f"/api/v1/recipes/{recipe_id}",
            headers=headers
        )
        assert get_response.status_code == 404
        
        logger.info("Recipe deleted successfully")
        
    except Exception as e:
        logger.error(f"Error in test_delete_recipe: {e}")
        raise

async def test_pagination(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试菜谱分页功能"""
    try:
        # 创建多个菜谱
        headers = {"Authorization": f"Bearer {test_user_token}"}
        for i in range(5):
            recipe_data = dict(test_recipe_data)
            recipe_data["title"] = f"测试菜谱 {i+1}"
            await test_client.post(
                "/api/v1/recipes/",
                json=recipe_data,
                headers=headers
            )
        
        # 测试分页
        logger.info("Testing pagination")
        response = await test_client.get(
            "/api/v1/recipes/",
            params={"page": 1, "per_page": 2},
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert len(data["recipes"]) == 2
        assert data["pagination"]["total"] >= 5
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 2
        
        logger.info("Pagination test completed successfully")
        
    except Exception as e:
        logger.error(f"Error in test_pagination: {e}")
        raise

async def test_filter_by_difficulty(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试按难度筛选菜谱"""
    try:
        # 创建不同难度的菜谱
        headers = {"Authorization": f"Bearer {test_user_token}"}
        difficulties = ["简单", "中等", "困难"]
        for difficulty in difficulties:
            recipe_data = dict(test_recipe_data)
            recipe_data["difficulty"] = difficulty
            await test_client.post(
                "/api/v1/recipes/",
                json=recipe_data,
                headers=headers
            )
        
        # 测试筛选
        logger.info("Testing difficulty filter")
        response = await test_client.get(
            "/api/v1/recipes/",
            params={"difficulty": "中等"},
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        recipes = data["recipes"]
        assert all(recipe["difficulty"] == "中等" for recipe in recipes)
        
        logger.info("Difficulty filter test completed successfully")
        
    except Exception as e:
        logger.error(f"Error in test_filter_by_difficulty: {e}")
        raise

async def test_filter_by_cuisine(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试按烹饪类型筛选菜谱"""
    try:
        # 创建不同类型的菜谱
        headers = {"Authorization": f"Bearer {test_user_token}"}
        cuisines = ["中餐", "西餐", "日料", "韩餐"]
        for cuisine in cuisines:
            recipe_data = dict(test_recipe_data)
            recipe_data["cuisine_type"] = cuisine
            await test_client.post(
                "/api/v1/recipes/",
                json=recipe_data,
                headers=headers
            )
        
        # 测试筛选
        logger.info("Testing cuisine type filter")
        response = await test_client.get(
            "/api/v1/recipes/",
            params={"cuisine_type": "日料"},
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        recipes = data["recipes"]
        assert all(recipe["cuisine_type"] == "日料" for recipe in recipes)
        
        logger.info("Cuisine type filter test completed successfully")
        
    except Exception as e:
        logger.error(f"Error in test_filter_by_cuisine: {e}")
        raise

async def test_get_nonexistent_recipe(test_client: AsyncClient, test_user_token: str):
    """测试获取不存在的菜谱"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        nonexistent_id = "00000000-0000-0000-0000-000000000000"
        
        logger.info(f"Attempting to get nonexistent recipe with id: {nonexistent_id}")
        response = await test_client.get(
            f"/api/v1/recipes/{nonexistent_id}",
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 404
        
        logger.info("Nonexistent recipe test completed successfully")
        
    except Exception as e:
        logger.error(f"Error in test_get_nonexistent_recipe: {e}")
        raise

async def test_update_others_recipe(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试更新他人的菜谱"""
    try:
        # 创建第二个用户
        user2_data = {
            "username": "testuser2",
            "password": "testPassword123!"
        }
        register_response = await test_client.post("/api/v1/auth/register", json=user2_data)
        if register_response.status_code != 201:
            logger.error(f"Failed to register user2: {register_response.json()}")
            raise ValueError("Failed to register user2")

        # 登录第二个用户
        login_response = await test_client.post(
            "/api/v1/auth/login/json",
            json={"username": user2_data["username"], "password": user2_data["password"]}
        )
        if login_response.status_code != 200:
            logger.error(f"Failed to login user2: {login_response.json()}")
            raise ValueError("Failed to login user2")

        login_data = login_response.json()
        user2_token = login_data["token"]["access_token"]
        if not user2_token:
            logger.error(f"Login response: {login_data}")
            raise ValueError("Failed to get access token for user2")
        
        # 用第一个用户创建菜谱
        headers1 = {"Authorization": f"Bearer {test_user_token}"}
        create_response = await test_client.post(
            "/api/v1/recipes/",
            json=test_recipe_data,
            headers=headers1
        )
        if create_response.status_code != 201:
            logger.error(f"Failed to create recipe: {create_response.json()}")
            raise ValueError("Failed to create recipe")

        recipe_id = create_response.json()["recipe"]["id"]
        
        # 用第二个用户尝试更新菜谱
        headers2 = {"Authorization": f"Bearer {user2_token}"}
        update_data = {"title": "未经授权的更新"}
        
        logger.info("Attempting to update recipe owned by another user")
        response = await test_client.put(
            f"/api/v1/recipes/{recipe_id}",
            json=update_data,
            headers=headers2
        )
        
        # 验证响应
        assert response.status_code == 403
        assert response.json()["detail"] == "FORBIDDEN"
        
        logger.info("Update others' recipe test completed successfully")
        
    except Exception as e:
        logger.error(f"Error in test_update_others_recipe: {e}")
        raise

async def test_duplicate_rating(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试重复评分"""
    try:
        # 创建菜谱
        headers = {"Authorization": f"Bearer {test_user_token}"}
        create_response = await test_client.post(
            "/api/v1/recipes/",
            json=test_recipe_data,
            headers=headers
        )
        recipe_id = create_response.json()["recipe"]["id"]
        
        # 第一次评分
        rating_data = {"rating": 4.5, "comment": "第一次评价"}
        await test_client.post(
            f"/api/v1/recipes/{recipe_id}/rate",
            json=rating_data,
            headers=headers
        )
        
        # 尝试重复评分
        logger.info("Attempting to rate recipe again")
        rating_data["comment"] = "重复评价"
        response = await test_client.post(
            f"/api/v1/recipes/{recipe_id}/rate",
            json=rating_data,
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 400
        
        logger.info("Duplicate rating test completed successfully")
        
    except Exception as e:
        logger.error(f"Error in test_duplicate_rating: {e}")
        raise

async def test_invalid_rating_value(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试无效的评分值"""
    try:
        # 创建菜谱
        headers = {"Authorization": f"Bearer {test_user_token}"}
        create_response = await test_client.post(
            "/api/v1/recipes/",
            json=test_recipe_data,
            headers=headers
        )
        recipe_id = create_response.json()["recipe"]["id"]
        
        # 测试评分值过高
        logger.info("Testing rating value too high")
        rating_data = {"rating": 6.0, "comment": "评分过高"}
        response = await test_client.post(
            f"/api/v1/recipes/{recipe_id}/rate",
            json=rating_data,
            headers=headers
        )
        assert response.status_code == 422
        
        # 测试评分值过低
        logger.info("Testing rating value too low")
        rating_data["rating"] = 0.0
        response = await test_client.post(
            f"/api/v1/recipes/{recipe_id}/rate",
            json=rating_data,
            headers=headers
        )
        assert response.status_code == 422
        
        logger.info("Invalid rating value test completed successfully")
        
    except Exception as e:
        logger.error(f"Error in test_invalid_rating_value: {e}")
        raise

async def test_combined_search_filter(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试多条件组合搜索和过滤"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 创建多个不同条件的菜谱
        recipes_data = [
            {**test_recipe_data, "title": "简单的中餐", "difficulty": "简单", "cuisine_type": "中餐", "cooking_time": 30},
            {**test_recipe_data, "title": "复杂的日料", "difficulty": "困难", "cuisine_type": "日料", "cooking_time": 60},
            {**test_recipe_data, "title": "中等的韩餐", "difficulty": "中等", "cuisine_type": "韩餐", "cooking_time": 45}
        ]
        
        for recipe in recipes_data:
            await test_client.post("/api/v1/recipes/", json=recipe, headers=headers)
        
        # 测试多条件组合搜索
        logger.info("Testing combined search and filter")
        response = await test_client.get(
            "/api/v1/recipes/",
            params={
                "keyword": "简单",
                "difficulty": "简单",
                "cuisine_type": "中餐",
                "max_cooking_time": 35
            },
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        recipes = data["recipes"]
        assert len(recipes) >= 1
        for recipe in recipes:
            assert recipe["difficulty"] == "简单"
            assert recipe["cuisine_type"] == "中餐"
            assert recipe["cooking_time"] <= 35
        
        logger.info("Combined search and filter test successful")
        
    except Exception as e:
        logger.error(f"Error in test_combined_search_filter: {e}")
        raise

async def test_recipe_extreme_values(test_client: AsyncClient, test_user_token: str):
    """测试菜谱极限值"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 准备极限值测试数据
        extreme_recipe = {
            "title": "极限测试菜谱" * 50,  # 超长标题
            "description": "描述" * 1000,  # 超长描述
            "ingredients": [{"name": f"食材{i}", "amount": "100克"} for i in range(100)],  # 大量食材
            "steps": [{"step": str(i), "description": "步骤描述"} for i in range(50)],  # 大量步骤
            "cooking_time": 999999,  # 极大烹饪时间
            "difficulty": "简单",
            "cuisine_type": "中餐"
        }
        
        # 测试创建极限值菜谱
        logger.info("Testing recipe with extreme values")
        response = await test_client.post(
            "/api/v1/recipes/",
            json=extreme_recipe,
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 422  # 应该返回验证错误
        
        logger.info("Extreme values test successful")
        
    except Exception as e:
        logger.error(f"Error in test_recipe_extreme_values: {e}")
        raise

async def test_recipe_data_integrity(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试菜谱数据完整性"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 创建原始菜谱
        create_response = await test_client.post(
            "/api/v1/recipes/",
            json=test_recipe_data,
            headers=headers
        )
        recipe_id = create_response.json()["recipe"]["id"]
        
        # 更新部分字段
        partial_update = {
            "title": "更新的标题"
        }
        
        # 测试部分更新
        logger.info("Testing partial recipe update")
        response = await test_client.patch(
            f"/api/v1/recipes/{recipe_id}",
            json=partial_update,
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 200
        updated_recipe = response.json()["recipe"]
        assert updated_recipe["title"] == partial_update["title"]
        # 验证其他字段保持不变
        assert updated_recipe["description"] == test_recipe_data["description"]
        assert updated_recipe["cooking_time"] == test_recipe_data["cooking_time"]
        
        # 测试删除用户后的菜谱状态
        # 创建新用户并创建菜谱
        new_user_data = {
            "username": "deletetest",
            "password": "Test@123456"
        }
        await test_client.post("/api/v1/auth/register", json=new_user_data)
        login_response = await test_client.post(
            "/api/v1/auth/login/json",
            json=new_user_data
        )
        new_token = login_response.json()["token"]["access_token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}
        
        # 用新用户创建菜谱
        new_recipe_response = await test_client.post(
            "/api/v1/recipes/",
            json=test_recipe_data,
            headers=new_headers
        )
        new_recipe_id = new_recipe_response.json()["recipe"]["id"]
        
        # 删除用户
        await test_client.delete(
            "/api/v1/auth/me",
            headers=new_headers
        )
        
        # 尝试获取该用户的菜谱
        response = await test_client.get(
            f"/api/v1/recipes/{new_recipe_id}",
            headers=headers  # 使用原始用户的token
        )
        
        # 验证菜谱状态
        assert response.status_code == 404  # 菜谱应该被删除
        
        logger.info("Recipe data integrity test successful")
        
    except Exception as e:
        logger.error(f"Error in test_recipe_data_integrity: {e}")
        raise

async def test_empty_search_params(test_client: AsyncClient, test_user_token: str):
    """测试空搜索参数"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 测试各种空或无效的搜索参数
        test_cases = [
            {"keyword": ""},
            {"keyword": "   "},
            {"difficulty": ""},
            {"cuisine_type": ""},
            {"keyword": None},
            {"max_cooking_time": "invalid"}
        ]
        
        for params in test_cases:
            logger.info(f"Testing search with params: {params}")
            response = await test_client.get(
                "/api/v1/recipes/",
                params=params,
                headers=headers
            )
            
            # 验证响应
            assert response.status_code in [200, 422]  # 应该返回成功或验证错误
            if response.status_code == 200:
                assert "recipes" in response.json()
            
        logger.info("Empty search params test successful")
        
    except Exception as e:
        logger.error(f"Error in test_empty_search_params: {e}")
        raise 