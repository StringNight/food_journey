"""运动相关功能的测试模块"""

import pytest
from httpx import AsyncClient
import logging
from datetime import datetime, timedelta, timezone
import asyncio

# 设置日志
logger = logging.getLogger(__name__)

# 标记所有测试为异步
pytestmark = pytest.mark.asyncio

@pytest.fixture
def test_workout_data():
    """创建测试训练数据"""
    return {
        "name": "测试训练",
        "notes": "这是一次测试训练",
        "duration": 60,  # 分钟
        "workout_date": datetime.now(timezone.utc).isoformat(),
        "exercises": [
            {
                "exercise_name": "深蹲",
                "exercise_type": "STRENGTH",
                "sets": 3,
                "reps": 12,
                "weight": 60.0,
                "duration": 0,
                "calories": 150
            },
            {
                "exercise_name": "跑步",
                "exercise_type": "CARDIO",
                "sets": 1,
                "reps": 1,
                "weight": 0.0,
                "duration": 20,
                "calories": 200
            }
        ]
    }

async def test_create_workout(test_client: AsyncClient, test_user_token: str, test_workout_data: dict):
    """测试创建训练记录功能"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 发送创建请求
        logger.info("Attempting to create workout")
        response = await test_client.post(
            "/api/v1/workouts",
            json=test_workout_data,
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 201
        data = response.json()
        assert data["schema_version"] == "1.0"
        workout = data["workout"]
        assert workout["name"] == test_workout_data["name"]
        assert workout["duration"] == test_workout_data["duration"]
        assert len(workout["exercises"]) == len(test_workout_data["exercises"])
        
        logger.info("Workout created successfully")
        
    except Exception as e:
        logger.error(f"Error in test_create_workout: {e}")
        raise

async def test_get_workout_list(test_client: AsyncClient, test_user_token: str, test_workout_data: dict):
    """测试获取训练记录列表功能"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 创建多个训练记录
        for i in range(3):
            workout_data = dict(test_workout_data)
            workout_data["name"] = f"测试训练 {i+1}"
            await test_client.post(
                "/api/v1/workouts",
                json=workout_data,
                headers=headers
            )
        
        # 获取训练列表
        logger.info("Attempting to get workout list")
        response = await test_client.get(
            "/api/v1/workouts",
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["schema_version"] == "1.0"
        assert len(data["workouts"]) >= 3
        assert "pagination" in data
        
        logger.info("Workout list retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error in test_get_workout_list: {e}")
        raise

async def test_update_workout(test_client: AsyncClient, test_user_token: str, test_workout_data: dict):
    """测试更新训练记录功能"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 创建训练记录
        create_response = await test_client.post(
            "/api/v1/workouts",
            json=test_workout_data,
            headers=headers
        )
        workout_id = create_response.json()["workout"]["id"]
        
        # 更新数据
        update_data = {
            "name": "更新后的训练",
            "notes": "这是更新后的训练记录",
            "duration": 90
        }
        
        # 发送更新请求
        logger.info(f"Attempting to update workout with id: {workout_id}")
        response = await test_client.put(
            f"/api/v1/workouts/{workout_id}",
            json=update_data,
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        workout = data["workout"]
        assert workout["name"] == update_data["name"]
        assert workout["notes"] == update_data["notes"]
        assert workout["duration"] == update_data["duration"]
        
        logger.info("Workout updated successfully")
        
    except Exception as e:
        logger.error(f"Error in test_update_workout: {e}")
        raise

async def test_get_workout_stats(test_client: AsyncClient, test_user_token: str, test_workout_data: dict):
    """测试获取训练统计数据"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 创建多个训练记录
        for i in range(5):
            workout_data = dict(test_workout_data)
            workout_data["workout_date"] = (datetime.now(timezone.utc) - timedelta(days=i)).isoformat()
            await test_client.post(
                "/api/v1/workouts",
                json=workout_data,
                headers=headers
            )
        
        # 获取统计数据
        logger.info("Attempting to get workout stats")
        start_date = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
        end_date = (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat()
        response = await test_client.get(
            "/api/v1/workouts/stats",
            params={
                "start_date": start_date,
                "end_date": end_date
            },
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["schema_version"] == "1.0"
        stats = data["stats"]
        assert stats["total_workouts"] == 5
        assert stats["total_duration"] == 300  # 5个训练 * 60分钟
        assert stats["strength_count"] == 5  # 每个训练都有一个力量训练
        assert stats["cardio_count"] == 5  # 每个训练都有一个有氧运动
        assert stats["flexibility_count"] == 0  # 没有柔韧性训练
        
        logger.info("Workout stats retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error in test_get_workout_stats: {e}")
        raise

async def test_filter_workouts(test_client: AsyncClient, test_user_token: str, test_workout_data: dict):
    """测试训练记录筛选功能"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 创建不同类型的训练记录
        workout_types = ["STRENGTH", "CARDIO", "FLEXIBILITY"]
        for workout_type in workout_types:
            workout_data = dict(test_workout_data)
            workout_data["exercises"][0]["exercise_type"] = workout_type
            await test_client.post(
                "/api/v1/workouts",
                json=workout_data,
                headers=headers
            )
        
        # 测试筛选
        logger.info("Testing workout type filter")
        response = await test_client.get(
            "/api/v1/workouts",
            params={"exercise_type": "STRENGTH"},
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        workouts = data["workouts"]
        assert any(
            exercise["exercise_type"] == "STRENGTH"
            for workout in workouts
            for exercise in workout["exercises"]
        )
        
        logger.info("Workout filter test successful")
        
    except Exception as e:
        logger.error(f"Error in test_filter_workouts: {e}")
        raise

async def test_invalid_workout_data(test_client: AsyncClient, test_user_token: str):
    """测试无效的训练数据处理"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 准备无效的训练数据
        invalid_workout_data = {
            "name": "",  # 空名称
            "duration": -1,  # 无效时长
            "exercises": []  # 空运动列表
        }
        
        # 尝试创建无效训练记录
        logger.info("Attempting to create workout with invalid data")
        response = await test_client.post(
            "/api/v1/workouts",
            json=invalid_workout_data,
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 422
        
        logger.info("Invalid workout data handled correctly")
        
    except Exception as e:
        logger.error(f"Error in test_invalid_workout_data: {e}")
        raise

async def test_date_range_filter(test_client: AsyncClient, test_user_token: str, test_workout_data: dict):
    """测试日期范围筛选功能"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 创建不同日期的训练记录
        dates = [
            datetime.now(timezone.utc),
            datetime.now(timezone.utc) - timedelta(days=1),
            datetime.now(timezone.utc) - timedelta(days=2),
            datetime.now(timezone.utc) - timedelta(days=7)
        ]
        
        for date in dates:
            workout_data = dict(test_workout_data)
            workout_data["workout_date"] = date.isoformat()
            await test_client.post(
                "/api/v1/workouts",
                json=workout_data,
                headers=headers
            )
        
        # 测试日期范围筛选
        start_date = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        end_date = datetime.now(timezone.utc).isoformat()
        
        logger.info("Testing date range filter")
        response = await test_client.get(
            "/api/v1/workouts",
            params={
                "start_date": start_date,
                "end_date": end_date
            },
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        workouts = data["workouts"]
        assert len(workouts) >= 3  # 应该至少有3个训练记录在范围内
        
        logger.info("Date range filter test successful")
        
    except Exception as e:
        logger.error(f"Error in test_date_range_filter: {e}")
        raise

async def test_invalid_exercise_type(test_client: AsyncClient, test_user_token: str, test_workout_data: dict):
    """测试无效的运动类型"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 准备包含无效运动类型的数据
        invalid_workout = dict(test_workout_data)
        invalid_workout["exercises"][0]["exercise_type"] = "INVALID_TYPE"
        
        # 尝试创建运动记录
        logger.info("Testing invalid exercise type")
        response = await test_client.post(
            "/api/v1/workouts",
            json=invalid_workout,
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 422
        
        logger.info("Invalid exercise type test successful")
        
    except Exception as e:
        logger.error(f"Error in test_invalid_exercise_type: {e}")
        raise

async def test_extreme_workout_values(test_client: AsyncClient, test_user_token: str):
    """测试运动记录的极限值"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 准备极限值测试数据
        extreme_workout = {
            "name": "极限测试运动" * 50,  # 超长名称
            "notes": "备注" * 1000,  # 超长备注
            "duration": 999999,  # 极大持续时间
            "workout_date": datetime.now(timezone.utc).isoformat(),
            "exercises": [
                {
                    "exercise_name": "测试运动",
                    "exercise_type": "STRENGTH",
                    "sets": 999,  # 极大组数
                    "reps": 999,  # 极大重复次数
                    "weight": 9999.99,  # 极大重量
                    "duration": -1,  # 负数持续时间
                    "calories": -100  # 负数卡路里
                }
            ]
        }
        
        # 测试创建极限值运动记录
        logger.info("Testing workout with extreme values")
        response = await test_client.post(
            "/api/v1/workouts",
            json=extreme_workout,
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 422
        
        logger.info("Extreme workout values test successful")
        
    except Exception as e:
        logger.error(f"Error in test_extreme_workout_values: {e}")
        raise

async def test_timezone_handling(test_client: AsyncClient, test_user_token: str, test_workout_data: dict):
    """测试时区处理"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 测试不同时区的日期
        timezones = [
            "2024-01-01T00:00:00+00:00",  # UTC
            "2024-01-01T00:00:00+08:00",  # UTC+8
            "2024-01-01T00:00:00-05:00",  # UTC-5
        ]
        
        for tz in timezones:
            workout_data = dict(test_workout_data)
            workout_data["workout_date"] = tz
            
            # 创建运动记录
            logger.info(f"Testing workout creation with timezone: {tz}")
            response = await test_client.post(
                "/api/v1/workouts",
                json=workout_data,
                headers=headers
            )
            
            # 验证响应
            assert response.status_code == 201
            created_workout = response.json()["workout"]
            # 验证返回的时间是UTC格式
            assert "Z" in created_workout["workout_date"] or "+00:00" in created_workout["workout_date"]
        
        logger.info("Timezone handling test successful")
        
    except Exception as e:
        logger.error(f"Error in test_timezone_handling: {e}")
        raise

async def test_concurrent_workout_update(test_client: AsyncClient, test_user_token: str, test_workout_data: dict):
    """测试并发更新运动记录"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 创建一个运动记录
        create_response = await test_client.post(
            "/api/v1/workouts",
            json=test_workout_data,
            headers=headers
        )
        workout_id = create_response.json()["workout"]["id"]
        
        # 准备并发更新
        async def update_workout(name: str):
            update_data = {
                "name": name,
                "notes": f"并发更新测试 - {name}"
            }
            return await test_client.put(
                f"/api/v1/workouts/{workout_id}",
                json=update_data,
                headers=headers
            )
        
        # 同时发送多个更新请求
        update_tasks = [
            update_workout(f"更新 {i}")
            for i in range(5)
        ]
        responses = await asyncio.gather(*update_tasks)
        
        # 验证响应
        success_count = sum(1 for r in responses if r.status_code == 200)
        conflict_count = sum(1 for r in responses if r.status_code == 409)
        
        # 应该只有一个成功，其他都是冲突
        assert success_count == 1
        assert conflict_count == 4
        
        logger.info("Concurrent workout update test successful")
        
    except Exception as e:
        logger.error(f"Error in test_concurrent_workout_update: {e}")
        raise

async def test_future_workout_date(test_client: AsyncClient, test_user_token: str, test_workout_data: dict):
    """测试未来日期的运动记录"""
    try:
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        # 准备未来日期的运动数据
        future_workout = dict(test_workout_data)
        future_workout["workout_date"] = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        
        # 尝试创建未来日期的运动记录
        logger.info("Testing future workout date")
        response = await test_client.post(
            "/api/v1/workouts",
            json=future_workout,
            headers=headers
        )
        
        # 验证响应
        assert response.status_code == 400
        assert "不能创建未来日期的运动记录" in response.json()["detail"]
        
        logger.info("Future workout date test successful")
        
    except Exception as e:
        logger.error(f"Error in test_future_workout_date: {e}")
        raise 