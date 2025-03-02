import httpx
import logging
from typing import Optional, Dict, List, Union, BinaryIO, Any, AsyncGenerator
import os
from dotenv import load_dotenv
from gradio_client import Client, handle_file
import json
from PIL import Image
import io
import base64
import tempfile
import asyncio
import time
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.user import UserProfileModel

load_dotenv()

class AIServiceClient:
    """AI服务客户端类
    
    负责与独立的AI服务进行通信，处理语音识别、LLM对话和图像识别请求
    """
    
    def __init__(self, api_url=None):
        # 保留原始初始化代码，但不实际连接
        self.api_url = api_url
        self.client = None
        self.logger = logging.getLogger(__name__)
        self.logger.info("AI服务客户端初始化成功 (Mock 模式)")
    
    async def chat_stream(self, messages):
        """模拟流式聊天响应"""
        # 模拟延迟
        await asyncio.sleep(0.5)
        
        # 模拟流式输出
        chunks = ["你", "好", "，", "我", "是", "AI", "助", "手", "。", "有", "什", "么", "可", "以", "帮", "助", "你", "的", "吗", "？"]
        for chunk in chunks:
            await asyncio.sleep(0.1)  # 模拟网络延迟
            yield chunk
    
    async def process_voice(self, voice_input):
        """模拟语音处理"""
        await asyncio.sleep(1)  # 模拟处理时间
        return "hello"
    
    async def recognize_food(self, image_path):
        """模拟食物识别"""
        await asyncio.sleep(1)  # 模拟处理时间
        return {
            "success": True,
            "food_items": [
                {"name": "苹果", "confidence": 0.95},
                {"name": "香蕉", "confidence": 0.85}
            ]
        }
    
    def extract_profile_updates(self, content):
        """模拟从AI回复中提取用户画像更新信息"""
        # 随机决定是否返回更新
        if random.random() > 0.7:
            return {
                "height": 175,
                "weight": 70,
                "health_goals": ["减肥", "增肌"]
            }
        return None
    
    async def process_profile_updates(self, user_id, updates, db):
        """模拟处理用户画像更新"""
        self.logger.info(f"模拟更新用户画像: {user_id}, 更新: {updates}")
        return True
    
    def _build_chat_messages(self, user_profile, current_message, chat_history=None):
        """构建聊天消息列表"""
        messages = [
            {"role": "system", "content": "你是一个健康饮食顾问。"},
            {"role": "user", "content": current_message}
        ]
        return messages

# 创建客户端实例
ai_client = AIServiceClient()
            
async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-r1:14b",
        max_tokens: int = 2000,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """发送流式聊天请求
        
        Args:
            messages: 消息历史
            model: 模型名称
            max_tokens: 最大token数
            user_profile: 用户画像信息（可选）
            
        Yields:
            str: 生成的文本片段
        """
        try:
            # 获取最后一条用户消息
            current_message = ""
            chat_history = []
            
            for msg in messages:
                if msg["role"] == "user":
                    current_message = msg["content"]
                else:
                    chat_history.append(msg)
            
            # 使用_build_chat_messages构建完整的消息列表
            full_messages = self._build_chat_messages(
                user_profile=user_profile or {},
                current_message=current_message,
                chat_history=chat_history
            )
            
            # 调用预测接口获取流式响应
            result = self.chat_client.submit(
                messages=full_messages,
                model=model,
                max_tokens=max_tokens,
                api_name="/chat_stream"
            )
            
            # 处理流式响应
            current = ""
            while True:
                try:
                    # 获取最新的输出
                    outputs = result.outputs()
                    if outputs is None:
                        # 如果outputs为None，等待一会再试
                        await asyncio.sleep(0.1)
                        continue
                        
                    # 确保outputs是列表且不为空
                    if not outputs:
                        await asyncio.sleep(0.1)
                        continue
                        
                    # 获取最新的文本
                    new_text = outputs[-1]
                    if not isinstance(new_text, str):
                        continue
                        
                    # 只产出新增的部分
                    if len(new_text) > len(current):
                        new_part = new_text[len(current):]
                        yield new_part
                        current = new_text
                    
                    # 检查是否已完成
                    if result.done():
                        break
                        
                    await asyncio.sleep(0.01)
                    
                except Exception as e:
                    logging.error(f"处理流式响应时发生错误: {e}")
                    break
                    
        except Exception as e:
            logging.error(f"流式聊天请求失败: {e}")
            raise
            
async def recognize_food(self, image_data: Union[str, BinaryIO, bytes]) -> Dict:
        """识别图片中的食物
        
        Args:
            image_data: 图片数据（文件路径、文件对象或字节数据）
            
        Returns:
            Dict: {
                "success": bool,
                "food_items": List[Dict],  # 包含识别结果
                "message": str  # 仅在success为false时出现
            }
        """
        try:
            # 1. 获取图片的二进制数据
            if isinstance(image_data, str):
                with open(image_data, 'rb') as f:
                    image_bytes = f.read()
            elif isinstance(image_data, BinaryIO):
                image_bytes = image_data.read()
            else:
                image_bytes = image_data
            
            # 2. 处理图片大小
            image_size = len(image_bytes)
            if image_size > 1024 * 1024:  # 如果大于1MB
                image = Image.open(io.BytesIO(image_bytes))
                max_size = 800
                ratio = min(max_size / image.width, max_size / image.height)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                output = io.BytesIO()
                image.save(output, format='JPEG', quality=75)
                image_bytes = output.getvalue()
            
            # 3. 转换为base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # 4. 调用食物识别服务
            result = self.food_client.predict(
                file=image_base64,
                api_name="/food_recognition"
            )
            
            if not result:
                return {
                    "success": False,
                    "message": "识别服务未返回结果"
                }
            
            # 5. 解析识别结果
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    # 如果不是JSON格式，假设是直接的食物名称
                    result = {"items": [{"name": result, "confidence": 1.0}]}
            
            return {
                "success": True,
                "food_items": result.get("items", [])
            }
            
        except Exception as e:
            logging.error(f"食物识别请求失败: {e}", exc_info=True)
            error_message = str(e)
            if "timeout" in error_message.lower():
                error_message = "请求超时，请稍后重试"
            elif "connection" in error_message.lower():
                error_message = "连接服务器失败，请检查网络连接"
            elif "decode" in error_message.lower():
                error_message = "图片格式不正确"
            elif "memory" in error_message.lower():
                error_message = "图片太大，请使用小一点的图片"
            
            return {
                "success": False,
                "message": f"食物识别失败: {error_message}"
            }
            
async def close(self):
        """关闭客户端连接"""
        # Gradio Client 会自动管理连接，不需要手动关闭
        pass 

def extract_profile_updates(self, response: str) -> Optional[Dict[str, Any]]:
        """从AI助手的回复中提取用户画像更新建议
        
        Args:
            response: AI助手的回复文本
            
        Returns:
            Optional[Dict[str, Any]]: 提取的更新建议，如果没有更新建议则返回None
        """
        try:
            # 查找更新建议部分
            start_marker = "===用户画像更新建议==="
            end_marker = "==================="
            
            if start_marker not in response or end_marker not in response:
                return None
                
            # 提取JSON部分
            start_idx = response.index(start_marker) + len(start_marker)
            end_idx = response.index(end_marker, start_idx)
            json_str = response[start_idx:end_idx].strip()
            
            # 解析JSON
            updates = json.loads(json_str)
            
            # 直接返回更新建议，不再强制要求包含 'update_reason' 字段，以支持所有新的用户画像字段
            return updates["updates"]
            
        except (ValueError, json.JSONDecodeError) as e:
            logging.error(f"解析用户画像更新建议失败: {e}")
            return None

async def process_profile_updates(
        self,
        user_id: str,
        updates: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """处理用户画像更新建议
        
        Args:
            user_id: 用户ID
            updates: 更新内容
            db: 数据库会话
            
        Returns:
            Dict[str, Any]: {
                "success": bool,
                "message": str,
                "updated_fields": List[str]  # 实际更新的字段列表
            }
        """
        try:
            # 1. 获取当前用户画像
            query = select(UserProfileModel).filter(UserProfileModel.user_id == user_id)
            result = await db.execute(query)
            profile = result.scalar_one_or_none()
            
            if not profile:
                # 如果用户画像不存在，创建新的
                profile = UserProfileModel(user_id=user_id)
                db.add(profile)
            
            # 2. 记录实际更新的字段
            updated_fields = []
            update_reason = updates.pop("update_reason", "AI助手建议的更新")
            
            # 3. 应用更新
            for field, value in updates.items():
                if hasattr(profile, field) and getattr(profile, field) != value:
                    setattr(profile, field, value)
                    updated_fields.append(field)
            
            if updated_fields:
                # 更新时间戳
                profile.updated_at = datetime.now()
                
                # 提交更改
                await db.commit()
                
                # 记录日志
                logging.info(
                    f"用户画像更新成功: user_id={user_id}, "
                    f"fields={updated_fields}, reason={update_reason}"
                )
                
                return {
                    "success": True,
                    "message": "用户画像更新成功",
                    "updated_fields": updated_fields
                }
            else:
                return {
                    "success": True,
                    "message": "用户画像无需更新",
                    "updated_fields": []
                }
                
        except Exception as e:
            logging.error(f"处理用户画像更新失败: {e}")
            # 回滚事务
            await db.rollback()
            return {
                "success": False,
                "message": f"用户画像更新失败: {str(e)}",
                "updated_fields": []
            }