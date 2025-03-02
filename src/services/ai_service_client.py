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
import random  # 添加这行导入
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
            
            # 记录日志
            logging.info(f"提取的JSON数据: {json_str}")
            
            try:
                # 解析JSON
                updates_data = json.loads(json_str)
                
                # 验证结构
                if not isinstance(updates_data, dict) or "updates" not in updates_data:
                    logging.warning(f"用户画像更新数据格式错误: {updates_data}")
                    return None
                
                # 获取更新数据
                updates = updates_data["updates"]
                
                # 类型转换和验证
                self._validate_and_convert_updates(updates)
                
                return updates
            except json.JSONDecodeError as e:
                logging.error(f"JSON解析错误: {e}, 原始文本: {json_str}")
                return None
                
        except Exception as e:
            logging.error(f"解析用户画像更新建议失败: {e}")
            return None
            
    def _validate_and_convert_updates(self, updates: Dict[str, Any]) -> None:
        """验证并转换更新数据的类型
        
        Args:
            updates: 更新数据字典
        """
        # 数值型字段列表
        numeric_fields = [
            "weight", "height", "body_fat_percentage", "muscle_mass", 
            "bmr", "tdee", "bmi", "water_ratio", "sleep_duration", 
            "deep_sleep_percentage", "goal_progress", "training_progress"
        ]
        
        # 整数型字段列表
        int_fields = [
            "age", "exercise_frequency", "fatigue_score", 
            "calorie_preference", "bmr", "tdee"
        ]
        
        # 列表型字段列表
        list_fields = [
            "health_goals", "health_conditions", "favorite_cuisines", 
            "dietary_restrictions", "allergies", "preferred_exercises", 
            "fitness_goals", "recovery_activities", "short_term_goals",
            "long_term_goals", "muscle_group_analysis"
        ]
        
        # 处理数值型字段
        for field in numeric_fields:
            if field in updates and updates[field] is not None:
                try:
                    updates[field] = float(updates[field])
                except (ValueError, TypeError):
                    logging.warning(f"字段 {field} 的值 {updates[field]} 无法转换为数值")
                    updates.pop(field, None)
        
        # 处理整数型字段
        for field in int_fields:
            if field in updates and updates[field] is not None:
                try:
                    updates[field] = int(float(updates[field]))
                except (ValueError, TypeError):
                    logging.warning(f"字段 {field} 的值 {updates[field]} 无法转换为整数")
                    updates.pop(field, None)
        
        # 处理列表型字段
        for field in list_fields:
            if field in updates and updates[field] is not None:
                if not isinstance(updates[field], list):
                    logging.warning(f"字段 {field} 的值不是列表类型: {updates[field]}")
                    updates.pop(field, None)
    
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
                
                # 3. 应用更新
                for field, value in updates.items():
                    # 检查字段是否存在于模型中
                    if hasattr(profile, field):
                        # 避免覆盖有效数据为None或空值
                        if value is not None and (
                            # 如果是列表类型，确保非空
                            (isinstance(value, list) and len(value) > 0) or
                            # 如果是字符串类型，确保非空
                            (isinstance(value, str) and value.strip()) or
                            # 其他类型直接使用
                            (not isinstance(value, (list, str)))
                        ):
                            # 检查值是否真的变化了
                            current_value = getattr(profile, field)
                            if current_value != value:
                                setattr(profile, field, value)
                                updated_fields.append(field)
                                logging.info(f"更新字段 '{field}': {current_value} -> {value}")
                
                if updated_fields:
                    # 更新时间戳
                    profile.updated_at = datetime.now()
                    
                    # 提交更改
                    await db.commit()
                    
                    # 记录日志
                    logging.info(
                        f"用户画像更新成功: user_id={user_id}, "
                        f"fields={updated_fields}"
                    )
                    
                    return {
                        "success": True,
                        "message": "用户画像更新成功",
                        "updated_fields": updated_fields
                    }
                else:
                    return {
                        "success": True,
                        "message": "没有需要更新的字段",
                        "updated_fields": []
                    }
                    
            except Exception as e:
                await db.rollback()
                error_message = f"用户画像更新失败: {str(e)}"
                logging.error(error_message)
                return {
                    "success": False,
                    "message": error_message,
                    "updated_fields": []
                }
    
    def _build_chat_messages(self, user_profile, current_message, chat_history=None):
        """构建聊天消息列表"""
        system_prompt = """你是美食之旅的AI智能顾问，一个结合营养科学、健身训练、烹饪艺术和健康管理的专业系统。你拥有以下专业领域的深厚知识和能力：

【营养学专业知识】
- 精通宏量营养素(蛋白质、碳水化合物、脂肪)与微量营养素(维生素、矿物质)平衡
- 能够根据用户的健康状况、目标和偏好设计个性化营养方案
- 掌握各类特殊饮食法(如生酮、间歇性断食、地中海饮食等)的科学原理与适用人群
- 能分析食物的营养成分、生物利用度与代谢通路

【健身与运动科学】
- 提供科学的力量训练、有氧运动、柔韧性训练和功能性训练指导
- 根据用户的体能水平和健身目标(增肌、减脂、增强耐力等)制定个性化训练计划
- 分析运动生理学原理，包括肌肉增长机制、能量系统与恢复原理
- 提供运动表现优化和伤病预防的专业建议

【烹饪技艺与食材科学】
- 精通全球各地烹饪技法，从基础刀工到复杂烹饪工艺
- 了解食材选择、储存和处理的最佳实践
- 能将营养科学原理应用于美食制作，平衡健康与美味
- 提供厨房设备使用、食谱改良和美食摄影的专业建议

【健康管理与生活方式优化】
- 整合睡眠质量、压力管理和心理健康因素
- 根据用户的生物节律和生活习惯提供个性化健康管理方案
- 分析用户健康数据，识别潜在风险因素和改进机会
- 提供科学的生活方式干预策略，促进整体健康

【个性化体验与进步追踪】
- 记录并分析用户的饮食、运动和健康数据的变化趋势
- 根据用户反馈不断调整和优化建议
- 提供激励性的进步反馈和行为改变策略
- 根据用户目标制定短期、中期和长期的可实现计划

【回答原则与限制】
- 仅回答与健康、营养、饮食、健身、烹饪和生活方式优化相关的问题
- 对于非相关领域的问题(如政治、娱乐、游戏等)，明确表示这超出了你的专业范围
- 不提供医疗诊断或取代专业医疗建议的内容
- 拒绝回答任何违反法律、伦理或可能对用户造成伤害的问题

【回答方式】
- 提供综合性回答，整合营养、健身、烹饪和健康管理的多个维度
- 确保建议相互协调，考虑各方面因素的相互作用和影响
- 使用科学证据支持观点，同时保持语言通俗易懂
- 在适当情况下提供具体、可操作的步骤或方案

在回答问题时，你会考虑用户的全面健康画像，包括身体状况、饮食偏好、运动习惯、烹饪技能和健康目标，确保建议真正满足用户的独特需求。你会优先考虑循证医学研究成果，同时保持友好、鼓励的沟通风格，激发用户持续进步的动力。

当用户提到以下数据时，请提取并按指定格式记录：

1. 身体数据：
   - 体重(weight): 数值，单位kg
   - 体脂率(body_fat_percentage): 数值，单位%
   - 肌肉量(muscle_mass): 数值，单位kg
   - 基础代谢率(bmr): 整数，单位kcal

2. 健身与锻炼数据：
   - 训练类型(training_type): 字符串，如"力量训练"、"跑步"等
   - 训练细节：包括组数(sets)、次数(reps)、重量(weight)等
   - 训练进度(training_progress): 数值，单位%
   - 健身目标(fitness_goals): 字符串列表
   - 短期目标(short_term_goals): 字符串列表
   - 长期目标(long_term_goals): 字符串列表
   - 目标进度(goal_progress): 数值，单位%
   - 肌肉群分析(muscle_group_analysis): 描述训练的肌肉群

3. 恢复与睡眠数据：
   - 睡眠时长(sleep_duration): 数值，单位小时
   - 深度睡眠比例(deep_sleep_percentage): 数值，单位%
   - 疲劳感评分(fatigue_score): 整数，范围1-5
   - 恢复活动(recovery_activities): 字符串列表，如"拉伸"、"瑜伽"等

4. 饮食与营养数据：
   - 每日卡路里摄入(daily_calories): 数值，单位kcal
   - 蛋白质摄入(protein_intake): 数值，单位g
   - 碳水化合物摄入(carbs_intake): 数值，单位g
   - 脂肪摄入(fat_intake): 数值，单位g
   - 水分摄入(water_intake): 数值，单位ml
   - 膳食模式(diet_pattern): 字符串，如"生酮饮食"、"间歇性断食"等
   - 食物偏好(food_preferences): 字符串列表
   - 进餐时间(meal_times): 时间列表

如果你识别到以上任何数据，请在回复的末尾添加下面的格式化内容：

===用户画像更新建议===
{
  "updates": {
    "weight": 数字,
    "body_fat_percentage": 数字,
    "muscle_mass": 数字,
    "bmr": 整数,
    "sleep_duration": 数字,
    "deep_sleep_percentage": 数字,
    "fatigue_score": 整数,
    "fitness_goals": ["目标1", "目标2", ...],
    "short_term_goals": ["目标1", "目标2", ...],
    "long_term_goals": ["目标1", "目标2", ...],
    "training_type": "训练类型",
    "training_progress": 数字,
    "goal_progress": 数字,
    "muscle_group_analysis": {"肌肉群": "分析"},
    "recovery_activities": ["活动1", "活动2", ...],
    "daily_calories": 数字,
    "protein_intake": 数字,
    "carbs_intake": 数字,
    "fat_intake": 数字,
    "water_intake": 数字,
    "diet_pattern": "饮食模式",
    "food_preferences": ["偏好1", "偏好2", ...],
    "meal_times": ["时间1", "时间2", ...],
    "extended_attributes": {
      "recovery_advice": "建议内容",
      "其他属性": "值"
    }
  }
}
===================

只包含用户实际提到的数据字段，数值必须精确，单位应转换为系统标准单位(kg, %, 小时等)。不要猜测或添加用户未明确提及的信息。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": current_message}
        ]
        
        # 如果有聊天历史，添加到消息中
        if chat_history:
            messages = [messages[0]] + chat_history + [messages[-1]]
            
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