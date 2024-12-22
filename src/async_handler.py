import asyncio
import aiohttp
from typing import Optional, Dict, List
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

class AsyncHandler:
    """异步处理器类
    
    处理需要异步执行的任务，如图片处理、搜索索引更新等。
    使用 aiohttp 进行异步HTTP请求，使用线程池处理同步任务。
    """
    
    def __init__(self):
        """初始化异步处理器
        
        创建线程池和aiohttp会话
        """
        self.executor = ThreadPoolExecutor(max_workers=4)  # 创建4个工作线程的线程池
        self.session = None  # aiohttp会话，延迟初始化
    
    async def get_session(self) -> aiohttp.ClientSession:
        """获取或创建 aiohttp 会话
        
        Returns:
            aiohttp.ClientSession: HTTP客户端会话
        """
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """关闭所有连接和资源
        
        关闭HTTP会话和线程池
        """
        if self.session and not self.session.closed:
            await self.session.close()
        self.executor.shutdown(wait=True)
    
    async def process_image(self, image_data: bytes) -> Dict:
        """异步处理图片
        
        Args:
            image_data: 图片二进制数据
            
        Returns:
            Dict: 处理结果
            
        Raises:
            Exception: 当图片处理失败时抛出
        """
        try:
            session = await self.get_session()
            # 调用图片处理API
            async with session.post(
                'http://image-processing-api/process',
                data={'image': image_data}
            ) as response:
                return await response.json()
        except Exception as e:
            logging.error(f"图片处理失败: {e}")
            return {'error': str(e)}
    
    async def process_recipe_creation(self,
                                    recipe_data: Dict,
                                    image_data: Optional[bytes] = None) -> Dict:
        """异步处理菜谱创建
        
        处理菜谱创建相关的所有异步任务，包括：
        1. 图片处理
        2. 搜索索引更新
        3. 订阅者通知
        
        Args:
            recipe_data: 菜谱数据
            image_data: 可选的图片数据
            
        Returns:
            Dict: 处理结果
        """
        tasks = []
        
        # 如果有图片，添加图片处理任务
        if image_data:
            tasks.append(self.process_image(image_data))
        
        # 添加其他异步任务
        tasks.extend([
            self._update_search_index(recipe_data),
            self._notify_subscribers(recipe_data)
        ])
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        processed_results = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logging.error(f"任务 {i} 失败: {result}")
            else:
                processed_results[f"task_{i}"] = result
        
        return processed_results
    
    async def _update_search_index(self, recipe_data: Dict) -> Dict:
        """更新搜索索引
        
        Args:
            recipe_data: 菜谱数据
            
        Returns:
            Dict: 更新结果
            
        Raises:
            Exception: 当更新失败时抛出
        """
        try:
            session = await self.get_session()
            async with session.post(
                'http://search-index-api/update',
                json=recipe_data
            ) as response:
                return await response.json()
        except Exception as e:
            logging.error(f"更新搜索索引失败: {e}")
            return {'error': str(e)}
    
    async def _notify_subscribers(self, recipe_data: Dict) -> Dict:
        """通知订阅者
        
        Args:
            recipe_data: 菜谱数据
            
        Returns:
            Dict: 通知结果
            
        Raises:
            Exception: 当通知失败时抛出
        """
        try:
            session = await self.get_session()
            async with session.post(
                'http://notification-api/notify',
                json=recipe_data
            ) as response:
                return await response.json()
        except Exception as e:
            logging.error(f"通知订阅者失败: {e}")
            return {'error': str(e)}
    
    def run_in_executor(self, func, *args):
        """在线程池中运行同步函数
        
        Args:
            func: 要执行的同步函数
            *args: 函数参数
            
        Returns:
            Any: 函数执行结果
        """
        return asyncio.get_event_loop().run_in_executor(
            self.executor, func, *args
        ) 