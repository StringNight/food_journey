"""菜谱收藏相关功能的测试模块"""

import pytest
from httpx import AsyncClient
import logging
from datetime import datetime
import uuid

# 设置日志
logger = logging.getLogger(__name__)

# 标记所有测试为异步
pytestmark = pytest.mark.asyncio

async def test_add_favorite(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试添加收藏功能"""
    try:
        # 创建一个菜谱
        headers = {"Authorization": f"Bearer {test_user_token}"}
        create_response = await test_client.post(
            "/api/v1/recipes/",
            json=test_recipe_data,
            headers=headers
        )
        recipe_id = create_response.json()["recipe"]["id"]
        
        # 添加到收藏
        logger.info(f"Attempting to add recipe {recipe_id} to favorites")
        response = await test_client.post(
            f"/api/v1/favorites/{recipe_id}",
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 201
        data = response.json()
        assert data["recipe_id"] == recipe_id
        assert "created_at" in data
        
        logger.info("Recipe added to favorites successfully")
        
    except Exception as e:
        logger.error(f"Error in test_add_favorite: {e}")
        raise

async def test_remove_favorite(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试取消收藏功能"""
    try:
        # 创建菜谱并添加到收藏
        headers = {"Authorization": f"Bearer {test_user_token}"}
        create_response = await test_client.post(
            "/api/v1/recipes/",
            json=test_recipe_data,
            headers=headers
        )
        recipe_id = create_response.json()["recipe"]["id"]
        
        # 添加到收藏
        await test_client.post(
            f"/api/v1/favorites/{recipe_id}",
            headers=headers
        )
        
        # 取消收藏
        logger.info(f"Attempting to remove recipe {recipe_id} from favorites")
        response = await test_client.delete(
            f"/api/v1/favorites/{recipe_id}",
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 204
        
        # 验证菜谱已从收藏列表中移除
        favorites_response = await test_client.get(
            "/api/v1/favorites/",
            headers=headers
        )
        favorites = favorites_response.json()["favorites"]
        assert not any(fav["recipe_id"] == recipe_id for fav in favorites)
        
        logger.info("Recipe removed from favorites successfully")
        
    except Exception as e:
        logger.error(f"Error in test_remove_favorite: {e}")
        raise

async def test_remove_nonexistent_favorite(test_client: AsyncClient, test_user_token: str):
    """测试取消不存在的收藏"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        nonexistent_id = "00000000-0000-0000-0000-000000000000"
        
        # 尝试取消不存在的收藏
        logger.info(f"Attempting to remove nonexistent favorite with id: {nonexistent_id}")
        response = await test_client.delete(
            f"/api/v1/favorites/{nonexistent_id}",
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 404
        
        logger.info("Remove nonexistent favorite test successful")
        
    except Exception as e:
        logger.error(f"Error in test_remove_nonexistent_favorite: {e}")
        raise

async def test_remove_others_favorite(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试删除其他用户的收藏"""
    try:
        # 创建第二个用户
        user2_data = {"username": "testuser2", "password": "Test@123456"}
        await test_client.post("/api/v1/auth/register", json=user2_data)
        
        # 使用第二个用户登录
        login_response = await test_client.post(
            "/api/v1/auth/login/json",
            json={
                "username": user2_data["username"],
                "password": user2_data["password"]
            }
        )
        
        assert login_response.status_code == 200
        user2_token = login_response.json()["token"]["access_token"]
        
        # 用第一个用户创建菜谱并收藏
        headers1 = {"Authorization": f"Bearer {test_user_token}"}
        create_response = await test_client.post(
            "/api/v1/recipes/",
            json=test_recipe_data,
            headers=headers1
        )
        recipe_id = create_response.json()["recipe"]["id"]
        
        await test_client.post(
            f"/api/v1/favorites/{recipe_id}",
            headers=headers1
        )
        
        # 用第二个用户尝试取消收藏
        headers2 = {"Authorization": f"Bearer {user2_token}"}
        logger.info("Attempting to remove favorite owned by another user")
        response = await test_client.delete(
            f"/api/v1/favorites/{recipe_id}",
            headers=headers2
        )
        
        # 验证响应
        assert response.status_code == 403
        
        logger.info("Remove others' favorite test successful")
        
    except Exception as e:
        logger.error(f"Error in test_remove_others_favorite: {e}")
        raise

async def test_get_favorites(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试获取收藏列表功能"""
    try:
        # 创建多个菜谱并添加到收藏
        headers = {"Authorization": f"Bearer {test_user_token}"}
        recipe_ids = []
        
        for i in range(3):
            recipe_data = dict(test_recipe_data)
            recipe_data["title"] = f"测试菜谱 {i+1}"
            create_response = await test_client.post(
                "/api/v1/recipes/",
                json=recipe_data,
                headers=headers
            )
            recipe_id = create_response.json()["recipe"]["id"]
            recipe_ids.append(recipe_id)
            
            await test_client.post(
                f"/api/v1/favorites/{recipe_id}",
                headers=headers
            )
        
        # 获取收藏列表
        logger.info("Attempting to get favorites list")
        response = await test_client.get(
            "/api/v1/favorites/",
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert len(data["favorites"]) >= 3
        # 验证返回的菜谱ID在我们创建的菜谱列表中
        assert all(fav["id"] in recipe_ids for fav in data["favorites"][:3])
        # 验证每个收藏项都包含必要的字段
        for fav in data["favorites"][:3]:
            assert "id" in fav
            assert "title" in fav
            assert "created_at" in fav
        
        logger.info("Favorites list retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error in test_get_favorites: {e}")
        raise

async def test_duplicate_favorite(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试重复收藏"""
    try:
        # 创建菜谱
        headers = {"Authorization": f"Bearer {test_user_token}"}
        create_response = await test_client.post(
            "/api/v1/recipes/",
            json=test_recipe_data,
            headers=headers
        )
        recipe_id = create_response.json()["recipe"]["id"]
        
        # 第一次收藏
        await test_client.post(
            f"/api/v1/favorites/{recipe_id}",
            headers=headers
        )
        
        # 尝试重复收藏
        logger.info("Attempting to add the same recipe to favorites again")
        response = await test_client.post(
            f"/api/v1/favorites/{recipe_id}",
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 400
        
        logger.info("Duplicate favorite test successful")
        
    except Exception as e:
        logger.error(f"Error in test_duplicate_favorite: {e}")
        raise

async def test_favorite_nonexistent_recipe(test_client: AsyncClient, test_user_token: str):
    """测试收藏不存在的菜谱"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        nonexistent_id = "00000000-0000-0000-0000-000000000000"
        
        # 尝试收藏不存在的菜谱
        logger.info(f"Attempting to favorite nonexistent recipe with id: {nonexistent_id}")
        response = await test_client.post(
            f"/api/v1/favorites/{nonexistent_id}",
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 404
        
        logger.info("Favorite nonexistent recipe test successful")
        
    except Exception as e:
        logger.error(f"Error in test_favorite_nonexistent_recipe: {e}")
        raise

async def test_get_favorites_pagination(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试收藏列表分页功能"""
    try:
        # 创建多个菜谱并添加到收藏
        headers = {"Authorization": f"Bearer {test_user_token}"}
        for i in range(5):
            recipe_data = dict(test_recipe_data)
            recipe_data["title"] = f"测试菜谱 {i+1}"
            create_response = await test_client.post(
                "/api/v1/recipes/",
                json=recipe_data,
                headers=headers
            )
            recipe_id = create_response.json()["recipe"]["id"]
            
            await test_client.post(
                f"/api/v1/favorites/{recipe_id}",
                headers=headers
            )
        
        # 测试分页
        logger.info("Testing favorites pagination")
        response = await test_client.get(
            "/api/v1/favorites/",
            params={"page": 1, "per_page": 2},
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert len(data["favorites"]) == 2
        assert data["pagination"]["total"] >= 5
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 2
        assert data["pagination"]["total_pages"] >= 3
        
        logger.info("Favorites pagination test successful")
        
    except Exception as e:
        logger.error(f"Error in test_get_favorites_pagination: {e}")
        raise

async def test_batch_favorite_operations(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试批量添加收藏"""
    try:
        # 创建多个菜谱
        headers = {"Authorization": f"Bearer {test_user_token}"}
        recipe_ids = []
        
        for i in range(3):
            recipe_data = dict(test_recipe_data)
            recipe_data["title"] = f"测试菜谱 {i+1}"
            create_response = await test_client.post(
                "/api/v1/recipes/",
                json=recipe_data,
                headers=headers
            )
            recipe_id = create_response.json()["recipe"]["id"]
            recipe_ids.append(recipe_id)
        
        # 批量添加收藏
        response = await test_client.post(
            "/api/v1/favorites/batch-add",
            headers=headers,
            json={"recipe_ids": recipe_ids}
        )
        
        # 验证响应
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "批量收藏成功"
        assert len(data["favorites"]) == len(recipe_ids)
        assert all(item["recipe_id"] in recipe_ids for item in data["favorites"])
        
        logger.info("Batch favorite operations test successful")
        
    except Exception as e:
        logger.error(f"Error in test_batch_favorite_operations: {e}")
        raise

async def test_favorite_limit(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试收藏数量限制"""
    try:
        # 创建11个菜谱
        headers = {"Authorization": f"Bearer {test_user_token}"}
        recipe_ids = []
        
        for i in range(11):
            recipe_data = dict(test_recipe_data)
            recipe_data["title"] = f"测试菜谱 {i+1}"
            create_response = await test_client.post(
                "/api/v1/recipes/",
                json=recipe_data,
                headers=headers
            )
            recipe_id = create_response.json()["recipe"]["id"]
            recipe_ids.append(recipe_id)
        
        # 尝试批量添加超过限制的收藏
        logger.info("Testing favorite limit with 11 recipes")
        response = await test_client.post(
            "/api/v1/favorites/batch-add",
            headers=headers,
            json={"recipe_ids": recipe_ids}
        )
        
        # 验证响应
        assert response.status_code == 400
        assert "每次最多只能收藏10个食谱" in response.json()["detail"]
        
        logger.info("Favorite limit test successful")
        
    except Exception as e:
        logger.error(f"Error in test_favorite_limit: {e}")
        raise

async def test_invalid_batch_operations(test_client: AsyncClient, test_user_token: str):
    """测试使用无效的食谱ID进行批量收藏"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        invalid_id = str(uuid.uuid4())
        
        # 尝试收藏不存在的菜谱
        logger.info(f"Testing batch favorite with invalid recipe ID: {invalid_id}")
        response = await test_client.post(
            "/api/v1/favorites/batch-add",
            headers=headers,
            json={"recipe_ids": [invalid_id]}
        )
        
        # 验证响应
        assert response.status_code == 400
        assert "不存在" in response.json()["detail"]
        
        logger.info("Invalid batch operations test successful")
        
    except Exception as e:
        logger.error(f"Error in test_invalid_batch_operations: {e}")
        raise

async def test_favorite_data_cleanup(test_client: AsyncClient, test_user_token: str, test_recipe_data: dict):
    """测试收藏数据清理"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 创建菜谱并收藏
        create_response = await test_client.post(
            "/api/v1/recipes/",
            json=test_recipe_data,
            headers=headers
        )
        recipe_id = create_response.json()["recipe"]["id"]
        
        await test_client.post(
            f"/api/v1/favorites/{recipe_id}",
            headers=headers
        )
        
        # 删除菜谱
        await test_client.delete(
            f"/api/v1/recipes/{recipe_id}",
            headers=headers
        )
        
        # 检查收藏列表
        logger.info("Checking favorites after recipe deletion")
        response = await test_client.get(
            "/api/v1/favorites/",
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        # 确保已删除的菜谱不在收藏列表中
        assert not any(fav["id"] == recipe_id for fav in data["favorites"])
        
        logger.info("Favorite data cleanup test successful")
        
    except Exception as e:
        logger.error(f"Error in test_favorite_data_cleanup: {e}")
        raise 