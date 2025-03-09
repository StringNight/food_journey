"""性能测试模块

测试系统在高负载情况下的性能表现
"""

import pytest
import logging
import asyncio
import time
from httpx import AsyncClient
from typing import List, Dict
import statistics
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
import os
import json

# 设置日志
logger = logging.getLogger(__name__)

# 标记所有测试为异步
pytestmark = pytest.mark.asyncio

# 性能测试参数
CONCURRENT_USERS = 10  # 并发用户数
REQUESTS_PER_USER = 5  # 每个用户的请求数
RECIPE_BATCH_SIZE = 20  # 一次批量创建的食谱数量

class TestEndpointPerformance:
    """测试API端点在高负载下的性能"""
    
    async def test_recipe_endpoint_performance(self, test_client: AsyncClient, test_user_token: str):
        """测试食谱相关端点的性能
        
        此测试会模拟多个并发用户同时访问食谱列表和详情页面
        """
        # 创建测试食谱
        recipe_ids = await self._create_test_recipes(test_client, test_user_token, RECIPE_BATCH_SIZE)
        assert len(recipe_ids) == RECIPE_BATCH_SIZE, f"应该创建 {RECIPE_BATCH_SIZE} 个测试食谱"
        
        # 模拟并发用户访问食谱列表
        list_response_times = await self._simulate_concurrent_requests(
            test_client, 
            "get_recipe_list", 
            CONCURRENT_USERS, 
            REQUESTS_PER_USER
        )
        
        # 模拟并发用户访问食谱详情
        detail_response_times = await self._simulate_concurrent_requests(
            test_client, 
            "get_recipe_detail", 
            CONCURRENT_USERS, 
            REQUESTS_PER_USER,
            recipe_ids=recipe_ids
        )
        
        # 生成性能报告
        self._generate_performance_report(
            "食谱端点性能测试", 
            {
                "食谱列表查询": list_response_times,
                "食谱详情查询": detail_response_times
            }
        )
        
        # 检查性能指标
        avg_list_time = statistics.mean(list_response_times)
        avg_detail_time = statistics.mean(detail_response_times)
        
        logger.info(f"食谱列表平均响应时间: {avg_list_time:.4f}秒")
        logger.info(f"食谱详情平均响应时间: {avg_detail_time:.4f}秒")
        
        # 性能断言 - 根据实际情况调整阈值
        assert avg_list_time < 0.5, f"食谱列表平均响应时间 ({avg_list_time:.4f}秒) 超过预期阈值 (0.5秒)"
        assert avg_detail_time < 0.2, f"食谱详情平均响应时间 ({avg_detail_time:.4f}秒) 超过预期阈值 (0.2秒)"
    
    async def test_search_performance(self, test_client: AsyncClient, test_user_token: str):
        """测试搜索功能的性能
        
        此测试会模拟多个并发用户同时进行不同关键词的搜索
        """
        # 创建测试数据
        keywords = ["健康", "简单", "快手", "减肥", "增肌", "早餐", "午餐", "晚餐", "甜点", "小吃"]
        
        # 模拟并发搜索请求
        search_response_times = await self._simulate_concurrent_requests(
            test_client, 
            "search_recipes", 
            CONCURRENT_USERS, 
            REQUESTS_PER_USER,
            keywords=keywords
        )
        
        # 生成性能报告
        self._generate_performance_report(
            "搜索功能性能测试", 
            {
                "食谱搜索": search_response_times
            }
        )
        
        # 检查性能指标
        avg_search_time = statistics.mean(search_response_times)
        logger.info(f"搜索功能平均响应时间: {avg_search_time:.4f}秒")
        
        # 性能断言
        assert avg_search_time < 0.5, f"搜索功能平均响应时间 ({avg_search_time:.4f}秒) 超过预期阈值 (0.5秒)"
    
    async def test_chat_api_performance(self, test_client: AsyncClient, test_user_token: str):
        """测试聊天API的性能
        
        此测试会模拟多个并发用户同时发送聊天请求
        """
        # 模拟并发聊天请求
        chat_response_times = await self._simulate_concurrent_requests(
            test_client, 
            "chat_request", 
            CONCURRENT_USERS // 2,  # 减少并发数以避免过度负载
            REQUESTS_PER_USER // 2,  # 减少请求数以避免过度负载
            token=test_user_token
        )
        
        # 生成性能报告
        self._generate_performance_report(
            "聊天API性能测试", 
            {
                "聊天请求": chat_response_times
            }
        )
        
        # 检查性能指标
        avg_chat_time = statistics.mean(chat_response_times)
        logger.info(f"聊天API平均响应时间: {avg_chat_time:.4f}秒")
        
        # 聊天API通常会较慢，所以阈值设置得更高
        assert avg_chat_time < 2.0, f"聊天API平均响应时间 ({avg_chat_time:.4f}秒) 超过预期阈值 (2.0秒)"
    
    # 辅助方法
    async def _create_test_recipes(self, client: AsyncClient, token: str, count: int) -> List[str]:
        """创建测试食谱"""
        recipe_ids = []
        headers = {"Authorization": f"Bearer {token}"}
        
        for i in range(count):
            recipe_data = {
                "title": f"性能测试食谱 {i+1}",
                "description": f"这是一个用于性能测试的食谱 {i+1}",
                "ingredients": [
                    {"name": "测试食材1", "amount": "100克"},
                    {"name": "测试食材2", "amount": "200克"}
                ],
                "steps": [
                    {"step": "1", "description": "测试步骤1"},
                    {"step": "2", "description": "测试步骤2"}
                ],
                "cooking_time": 30,
                "difficulty": "简单",
                "cuisine_type": "测试"
            }
            
            response = await client.post(
                "/api/v1/recipes/create_recipe",
                json=recipe_data,
                headers=headers
            )
            
            if response.status_code == 201:
                recipe_ids.append(response.json()["recipe"]["id"])
            else:
                logger.error(f"创建测试食谱失败: {response.text}")
        
        return recipe_ids
    
    async def _simulate_concurrent_requests(
        self, 
        client: AsyncClient, 
        request_type: str, 
        num_users: int, 
        requests_per_user: int,
        **kwargs
    ) -> List[float]:
        """模拟并发请求并测量响应时间"""
        response_times = []
        
        async def make_request(user_id: int):
            for req_id in range(requests_per_user):
                start_time = time.time()
                
                try:
                    if request_type == "get_recipe_list":
                        response = await client.get(
                            "/api/v1/recipes/",
                            params={"page": req_id % 5 + 1, "per_page": 20}
                        )
                    elif request_type == "get_recipe_detail":
                        # 随机选择一个食谱ID
                        recipe_id = kwargs.get("recipe_ids", [])[req_id % len(kwargs.get("recipe_ids", []))]
                        response = await client.get(f"/api/v1/recipes/{recipe_id}")
                    elif request_type == "search_recipes":
                        # 随机选择一个关键词
                        keyword = kwargs.get("keywords", [])[req_id % len(kwargs.get("keywords", []))]
                        response = await client.get(
                            "/api/v1/recipes/",
                            params={"keyword": keyword, "page": 1, "per_page": 20}
                        )
                    elif request_type == "chat_request":
                        headers = {"Authorization": f"Bearer {kwargs.get('token')}"}
                        chat_data = {
                            "messages": [
                                {"role": "system", "content": "You are a helpful assistant."},
                                {"role": "user", "content": f"请推荐一道简单的菜谱，用户 {user_id}，请求 {req_id}"}
                            ],
                            "model": "qwen2.5:14b",
                            "max_tokens": 100  # 减少令牌数以加快响应速度
                        }
                        response = await client.post(
                            "/api/v1/chat/text",
                            json=chat_data,
                            headers=headers
                        )
                    else:
                        raise ValueError(f"未知的请求类型: {request_type}")
                    
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    
                    if response.status_code < 400:  # 只记录成功的请求
                        response_times.append(elapsed_time)
                    else:
                        logger.error(f"请求失败: {response.status_code} - {response.text}")
                
                except Exception as e:
                    logger.error(f"请求异常: {str(e)}")
        
        # 创建并发任务
        tasks = [make_request(user_id) for user_id in range(num_users)]
        await asyncio.gather(*tasks)
        
        return response_times
    
    def _generate_performance_report(self, title: str, data: Dict[str, List[float]]):
        """生成性能测试报告"""
        try:
            # 创建图表
            plt.figure(figsize=(10, 6))
            
            # 计算统计数据
            stats = {}
            for name, times in data.items():
                if times:
                    stats[name] = {
                        "min": min(times),
                        "max": max(times),
                        "avg": statistics.mean(times),
                        "median": statistics.median(times),
                        "p95": statistics.quantiles(times, n=20)[18],  # 95th percentile
                        "std_dev": statistics.stdev(times) if len(times) > 1 else 0
                    }
                    
                    # 绘制响应时间分布
                    plt.hist(times, bins=20, alpha=0.7, label=name)
            
            plt.title(f"{title} - 响应时间分布")
            plt.xlabel("响应时间 (秒)")
            plt.ylabel("请求数")
            plt.legend()
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # 保存图表
            reports_dir = os.path.join(os.path.dirname(__file__), "..", "performance_reports")
            os.makedirs(reports_dir, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            plt.savefig(os.path.join(reports_dir, f"{title.replace(' ', '_')}_{timestamp}.png"))
            
            # 保存统计数据
            with open(os.path.join(reports_dir, f"{title.replace(' ', '_')}_{timestamp}.json"), 'w') as f:
                json.dump(stats, f, indent=2)
            
            # 打印统计数据
            for name, stat in stats.items():
                logger.info(f"{name} 性能统计:")
                logger.info(f"  最小响应时间: {stat['min']:.4f}秒")
                logger.info(f"  最大响应时间: {stat['max']:.4f}秒")
                logger.info(f"  平均响应时间: {stat['avg']:.4f}秒")
                logger.info(f"  中位响应时间: {stat['median']:.4f}秒")
                logger.info(f"  95%响应时间: {stat['p95']:.4f}秒")
                logger.info(f"  标准差: {stat['std_dev']:.4f}")
            
        except Exception as e:
            logger.error(f"生成性能报告失败: {str(e)}")


class TestEndpointStability:
    """测试API端点的稳定性"""
    
    async def test_continuous_access(self, test_client: AsyncClient, test_user_token: str):
        """测试持续访问API的稳定性
        
        此测试会持续发送请求一段时间，检查系统稳定性
        """
        # 测试参数
        test_duration = 60  # 测试持续时间（秒）
        request_interval = 0.5  # 请求间隔（秒）
        
        headers = {"Authorization": f"Bearer {test_user_token}"}
        start_time = time.time()
        end_time = start_time + test_duration
        
        success_count = 0
        error_count = 0
        response_times = []
        
        logger.info(f"开始持续访问测试，持续 {test_duration} 秒")
        
        # 创建一个测试食谱
        recipe_data = {
            "title": "稳定性测试食谱",
            "description": "这是一个用于稳定性测试的食谱",
            "ingredients": [
                {"name": "测试食材", "amount": "100克"}
            ],
            "steps": [
                {"step": "1", "description": "测试步骤"}
            ],
            "cooking_time": 10,
            "difficulty": "简单",
            "cuisine_type": "测试"
        }
        
        response = await test_client.post(
            "/api/v1/recipes/create_recipe",
            json=recipe_data,
            headers=headers
        )
        
        assert response.status_code == 201, "创建测试食谱失败"
        recipe_id = response.json()["recipe"]["id"]
        
        # 持续发送请求
        while time.time() < end_time:
            try:
                req_start_time = time.time()
                
                # 轮流访问不同端点
                endpoint_index = int((time.time() - start_time) / request_interval) % 5
                
                if endpoint_index == 0:
                    # 获取食谱列表
                    response = await test_client.get("/api/v1/recipes/")
                elif endpoint_index == 1:
                    # 获取食谱详情
                    response = await test_client.get(f"/api/v1/recipes/{recipe_id}")
                elif endpoint_index == 2:
                    # 搜索食谱
                    response = await test_client.get(
                        "/api/v1/recipes/",
                        params={"keyword": "测试", "page": 1}
                    )
                elif endpoint_index == 3:
                    # 获取用户资料
                    response = await test_client.get(
                        "/api/v1/profile",
                        headers=headers
                    )
                else:
                    # 简单聊天请求
                    chat_data = {
                        "messages": [
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": "你好"}
                        ],
                        "model": "qwen2.5:14b",
                        "max_tokens": 50
                    }
                    response = await test_client.post(
                        "/api/v1/chat/text",
                        json=chat_data,
                        headers=headers
                    )
                
                req_end_time = time.time()
                elapsed_time = req_end_time - req_start_time
                
                if response.status_code < 400:
                    success_count += 1
                    response_times.append(elapsed_time)
                else:
                    error_count += 1
                    logger.error(f"请求失败: {response.status_code} - {response.text}")
                
                # 等待一段时间再发送下一个请求
                await asyncio.sleep(request_interval)
                
            except Exception as e:
                error_count += 1
                logger.error(f"请求异常: {str(e)}")
                await asyncio.sleep(request_interval)
        
        # 计算成功率和性能指标
        total_requests = success_count + error_count
        success_rate = (success_count / total_requests) * 100 if total_requests > 0 else 0
        
        logger.info(f"持续访问测试完成:")
        logger.info(f"  总请求数: {total_requests}")
        logger.info(f"  成功请求数: {success_count}")
        logger.info(f"  错误请求数: {error_count}")
        logger.info(f"  成功率: {success_rate:.2f}%")
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            logger.info(f"  平均响应时间: {avg_response_time:.4f}秒")
            logger.info(f"  最大响应时间: {max_response_time:.4f}秒")
            logger.info(f"  最小响应时间: {min_response_time:.4f}秒")
        
        # 稳定性断言
        assert success_rate > 95, f"API稳定性测试成功率 ({success_rate:.2f}%) 低于预期阈值 (95%)"
        if response_times:
            assert avg_response_time < 1.0, f"API稳定性测试平均响应时间 ({avg_response_time:.4f}秒) 超过预期阈值 (1.0秒)" 