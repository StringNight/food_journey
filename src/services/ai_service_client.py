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
    
    def __init__(self):
        """初始化AI服务客户端"""
        # 初始化各个服务的客户端
        self.chat_client = Client(
            os.getenv("CHAT_SERVICE_URL", "https://gradio.infsols.com/")
        )
        self.voice_client = Client(
            os.getenv("VOICE_SERVICE_URL", "https://gradio.infsols.com/")
        )
        self.food_client = Client(
            os.getenv("FOOD_SERVICE_URL", "https://gradio.infsols.com/")
        )
        
        logging.info("AI服务客户端初始化成功")
        
    async def process_voice(self, audio_file: Union[str, BinaryIO, bytes]) -> str:
        """处理语音文件，转写为文本
        
        参数:
            audio_file: 音频文件路径或URL
        返回:
            str: 识别出的文本
        """
        try:
            # 如果是文件路径，转换为numpy格式
            if isinstance(audio_file, str):
                if audio_file.startswith("/uploads/voices/"):
                    # 将相对路径转换为完整URL
                    audio_url = f"{os.getenv('BASE_URL', 'http://localhost:8000')}{audio_file}"
                    logging.info(f"处理语音文件URL: {audio_url}")
                else:
                    audio_url = audio_file
                    logging.info(f"处理外部语音URL: {audio_url}")
                
                try:
                    # 将音频文件转换为numpy格式
                    import scipy.io.wavfile
                    import numpy as np
                    
                    # 下载文件到临时位置
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                        if audio_url.startswith(('http://', 'https://')):
                            # 如果是URL，下载文件
                            with httpx.stream('GET', audio_url) as r:
                                for chunk in r.iter_bytes():
                                    temp_file.write(chunk)
                        else:
                            # 如果是本地文件路径，直接复制
                            with open(audio_url, 'rb') as src_file:
                                temp_file.write(src_file.read())
                        temp_path = temp_file.name
                    
                    # 读取音频文件为numpy格式
                    sample_rate, audio_array = scipy.io.wavfile.read(temp_path)
                    logging.info(f"音频文件转换为numpy格式: 采样率={sample_rate}, 形状={audio_array.shape}")
                    
                    # 调用语音识别服务，传递numpy格式
                    result = self.voice_client.predict(
                        audio=(sample_rate, audio_array),
                        api_name="/voice_transcribe"
                    )
                    logging.info(f"语音识别结果: {result}")
                    
                    # 清理临时文件
                    try:
                        os.unlink(temp_path)
                        logging.info(f"临时文件已删除: {temp_path}")
                    except Exception as e:
                        logging.warning(f"临时文件删除失败: {str(e)}")
                        
                except Exception as e:
                    logging.error(f"音频转换或语音识别服务调用失败: {str(e)}")
                    raise ValueError(f"语音识别服务调用失败: {str(e)}")
                
                if isinstance(result, dict):
                    if "error" in result:
                        raise ValueError(f"语音识别失败: {result['error']}")
                    return result.get("text", "")
                return str(result)
                
            elif isinstance(audio_file, (bytes, BinaryIO)):
                logging.info("处理二进制音频数据")
                # 如果是字节数据或文件对象，保存为临时文件
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    if isinstance(audio_file, bytes):
                        temp_file.write(audio_file)
                    else:
                        temp_file.write(audio_file.read())
                    temp_path = temp_file.name
                    logging.info(f"临时文件保存至: {temp_path}")
                
                try:
                    # 将音频文件转换为numpy格式
                    import scipy.io.wavfile
                    import numpy as np
                    
                    # 读取音频文件为numpy格式
                    sample_rate, audio_array = scipy.io.wavfile.read(temp_path)
                    logging.info(f"音频文件转换为numpy格式: 采样率={sample_rate}, 形状={audio_array.shape}")
                    
                    # 调用语音识别服务，传递numpy格式
                    result = self.voice_client.predict(
                        audio=(sample_rate, audio_array),
                        api_name="/voice_transcribe"
                    )
                    logging.info(f"语音识别结果: {result}")
                    
                except Exception as e:
                    logging.error(f"音频转换或语音识别服务调用失败: {str(e)}")
                    raise ValueError(f"语音识别服务调用失败: {str(e)}")
                finally:
                    # 清理临时文件
                    try:
                        os.unlink(temp_path)
                        logging.info(f"临时文件已删除: {temp_path}")
                    except Exception as e:
                        logging.warning(f"临时文件删除失败: {str(e)}")
                
                if isinstance(result, dict):
                    if "error" in result:
                        raise ValueError(f"语音识别失败: {result['error']}")
                    return result.get("text", "")
                return str(result)
            
            else:
                raise ValueError("不支持的音频输入类型")
                
        except Exception as e:
            logging.error(f"语音识别失败: {str(e)}")
            raise ValueError(f"语音识别失败: {str(e)}")
            
    def _build_chat_messages(
        self,
        user_profile: Dict[str, Any],
        current_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """构建聊天消息列表
        
        Args:
            user_profile: 用户画像信息
            current_message: 当前用户消息
            chat_history: 历史对话记录
            
        Returns:
            List[Dict[str, str]]: 构建好的消息列表
        """
        messages = []
        
        # 1. 添加系统提示词
        system_prompt = """你是一名专业的营养学家、健康管理师和运动指导专家。请基于用户画像和对话内容，为用户提供全方位的健康生活指导方案。

0. 用户画像更新：
   - 识别用户提供的新信息，包括但不限于：
     * 身高、体重的变化
     * 新的健康状况或症状
     * 饮食习惯的改变
     * 运动习惯的变化
     * 新的过敏反应
     * 生活方式的调整
     * 健康目标的更新
   - 分析用户的行为变化
   - 及时更新相关建议
   - 如果发现需要更新用户画像，请在回复消息的最后部分使用以下格式提供更新建议（以===用户画像更新建议===开始，到===================结束，严格遵守格式要求，不要有任何其它额外标记信息，如```Json等）：
===用户画像更新建议===
{
    "updates": {
        "birth_date": "2024-01-11",  // 可选
        "gender": "string",  // 可选，枚举值：男|女|其他
        "height": 170.0,  // 可选，单位：厘米
        "weight": 65.0,  // 可选，单位：千克
        "body_fat_percentage": 20.0,  // 可选，单位：%
        "muscle_mass": 50.0,  // 可选，单位：千克
        "health_conditions": ["高血压", "糖尿病"],  // 可选
        "health_goals": ["减重", "增肌"],  // 可选
        "cooking_skill_level": "初级",  // 可选，枚举值：初级|中级|高级
        "favorite_cuisines": ["中餐", "日料"],  // 可选
        "dietary_restrictions": ["无麸质", "素食"],  // 可选
        "allergies": ["花生", "海鲜"],  // 可选
        "calorie_preference": 2000,  // 可选，单位：卡路里
        "nutrition_goals": {  // 可选
            "protein": 150,  // 单位：克
            "carbs": 200,  // 单位：克
            "fat": 60  // 单位：克
        },
        "fitness_level": "中级",  // 可选，枚举值：初级|中级|高级
        "exercise_frequency": 3,  // 可选，范围：0-7
        "preferred_exercises": ["跑步", "力量训练"],  // 可选
        "fitness_goals": ["增肌", "提高耐力"],  // 可选
        "update_reason": "基于用户提供的信息..."  // 必填，更新原因说明
    }
}
===================

营养建议要点：
1. 宏量营养素分配：
   - 根据用户的BMI、体脂率和运动水平，计算每日所需的蛋白质、碳水化合物和脂肪比例
   - 考虑用户的运动强度和时间，调整碳水化合物的补充时机
   - 确保优质蛋白的摄入，推荐具体的蛋白质来源

2. 微量营养素补充：
   - 基于用户的健康状况和营养目标，建议所需的维生素和矿物质补充
   - 推荐富含特定营养素的食材
   - 注意可能的营养素相互作用

3. 膳食规划：
   - 设计符合用户口味和烹饪水平的食谱
   - 考虑用户的饮食限制和过敏原
   - 提供详细的食材选购指南和烹饪方法
   - 建议适合的进餐时间和份量

健康管理建议：
1. 体重管理：
   - 根据用户的BMI和体脂率，制定合理的体重目标
   - 设计可持续的减重/增重计划
   - 建议每周体重监测频率

2. 健康风险评估：
   - 分析用户现有的健康问题
   - 评估潜在的健康风险
   - 提供针对性的预防建议

3. 生活方式指导：
   - 作息时间建议
   - 压力管理方法
   - 饮水建议
   - 建议戒除不良习惯

运动指导方案：
1. 有氧运动：
   - 根据用户的体能水平推荐合适的有氧运动
   - 指导心率控制范围
   - 建议运动时长和频率

2. 力量训练：
   - 设计适合用户水平的训练计划
   - 推荐具体的动作和组数
   - 注意动作要领和安全事项

3. 运动营养策略：
   - 运动前后的营养补充建议
   - 运动期间的补水方案
   - 恢复期的营养摄入指导

回复要求：
1. 专业性：
   - 使用准确的专业术语
   - 提供科学依据
   - 引用权威研究或指南（如有）

2. 个性化：
   - 充分考虑用户的个人情况和限制
   - 根据用户的生活方式调整建议
   - 考虑实施建议的可行性

3. 安全性：
   - 注意可能的禁忌症
   - 提醒潜在风险
   - 建议必要时咨询医生

4. 动态调整：
   - 根据用户反馈调整方案
   - 设定阶段性目标
   - 提供进展监测方法

5. 输入处理：
   - 对于图片输入：分析食物的营养价值，评估是否符合用户的健康目标
   - 对于语音输入：确保回复简明易懂，适合口头表达
   - 对于文字输入：提供详细的专业建议和具体的执行方案

7. 非相关问题处理：
   - 礼貌地说明你只能回答与饮食、营养、运动、健康相关的问题
   - 不要给出任何非饮食、营养、运动、健康相关的问题的回答
   - 引导用户询问相关领域的问题
   - 如果问题部分相关，尽量从健康角度给出建议

请确保每次回复都体现专业性、针对性和全面性，帮助用户建立健康的生活方式。如果用户询问与饮食、营养、运动、健康无关的问题，请礼貌地说明你的专业范围并建议用户寻求相关领域的专家帮助。"""
        
        # 检查历史消息中是否已包含系统消息
        has_system_msg = False
        if chat_history:
            for msg in chat_history:
                if msg.get("role") == "system":
                    has_system_msg = True
                    break
        
        # 只有在历史消息不包含系统消息时才添加
        if not has_system_msg:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
            # 2. 添加用户画像信息
            if user_profile:
                profile_str = f"""用户画像信息：
- 性别：{user_profile.get('gender', '未知')}
- 年龄：{user_profile.get('age', '未知')}岁
- 身高：{user_profile.get('height', '未知')}cm
- 体重：{user_profile.get('weight', '未知')}kg
- BMI：{user_profile.get('bmi', '未知')}
- 体脂率：{user_profile.get('body_fat_percentage', '未知')}%
- 健康状况：{', '.join(user_profile.get('health_conditions', ['无']))}
- 健康目标：{', '.join(user_profile.get('health_goals', ['无']))}
- 饮食偏好：{', '.join(user_profile.get('food_preferences', ['无']))}
- 饮食限制：{', '.join(user_profile.get('dietary_restrictions', ['无']))}
- 食物过敏：{', '.join(user_profile.get('allergies', ['无']))}
- 烹饪水平：{user_profile.get('cooking_level', '初级')}
- 营养目标：{', '.join(user_profile.get('nutrition_goals', ['无']))}
- 健身水平：{user_profile.get('fitness_level', '未知')}
- 运动频率：每周{user_profile.get('exercise_frequency', '未知')}次
- 健身目标：{', '.join(user_profile.get('fitness_goals', ['无']))}"""
                
                messages.append({
                    "role": "system",
                    "content": profile_str
                })
        
        # 3. 添加历史对话记录
        if chat_history:
            messages.extend(chat_history)
        
        # 4. 添加当前用户消息
        messages.append({
            "role": "user",
            "content": current_message
        })
        
        # 记录最终构建的消息列表
        logging.debug(f"构建的完整消息列表: {json.dumps(messages, ensure_ascii=False)}")
        
        return messages
            
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "qwen2.5:14b",
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
            # 检查消息列表是否为空
            if not messages:
                yield "请提供消息"
                return
                
            # 分离系统消息、用户消息和助手消息
            system_messages = [msg for msg in messages if msg["role"] == "system"]
            user_messages = [msg for msg in messages if msg["role"] == "user"]
            assistant_messages = [msg for msg in messages if msg["role"] == "assistant"]
            
            if not user_messages:
                yield "请提供用户消息"
                return
                
            # 获取最后一条用户消息作为当前消息
            current_message = user_messages[-1]["content"]
            
            # 方法一：直接使用传入的完整消息列表发送到模型（保留所有历史）
            # 这种方式会保留原始的消息顺序和内容
            full_messages = messages
            
            # 方法二：使用_build_chat_messages构建消息列表
            # 这种方式会根据需要添加系统提示词和用户画像，但可能改变消息顺序
            # 如果需要使用这种方式，请取消下面的注释并注释掉上面的"方法一"

            # # 过滤掉最后一条用户消息，因为它将单独处理
            # chat_history = [msg for msg in messages if msg != user_messages[-1]]
            # full_messages = self._build_chat_messages(
            #     user_profile=user_profile or {},
            #     current_message=current_message,
            #     chat_history=chat_history
            # )
            
            # 记录发送给模型的消息，便于调试
            logging.debug(f"发送给模型的完整消息: {json.dumps(full_messages, ensure_ascii=False)}")
            
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
            # 记录完整的响应以便调试
            logging.info(f"尝试从以下AI回复中提取用户画像更新建议: {response[:200]}...")
            
            # 查找更新建议部分
            start_marker = "===用户画像更新建议==="
            end_marker = "==================="
            
            if start_marker not in response:
                logging.info(f"未找到用户画像更新建议开始标记: '{start_marker}'")
                return None
                
            if end_marker not in response:
                logging.info(f"未找到用户画像更新建议结束标记: '{end_marker}'")
                return None
                
            # 提取JSON部分
            start_idx = response.index(start_marker) + len(start_marker)
            end_idx = response.index(end_marker, start_idx)
            json_str = response[start_idx:end_idx].strip()
            
            # 记录提取到的JSON字符串
            logging.info(f"从AI回复中提取到用户画像更新建议: {json_str}")
            
            try:
                # 解析JSON
                updates = json.loads(json_str)
                
                if "updates" not in updates:
                    logging.error(f"用户画像更新JSON缺少'updates'字段: {json_str}")
                    return None
                
                # 记录解析后的更新内容
                logging.info(f"解析后的用户画像更新: {updates['updates']}")
                
                # 直接返回更新建议，不再强制要求包含 'update_reason' 字段，以支持所有新的用户画像字段
                return updates["updates"]
            except json.JSONDecodeError as json_err:
                logging.error(f"解析用户画像更新JSON失败: {str(json_err)}, 原始字符串: {json_str}")
                return None
            
        except Exception as e:
            logging.error(f"提取用户画像更新建议失败: {str(e)}, 响应内容: {response[:200]}...")
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
            db: 数据库会话（由调用者提供和管理）
            
        Returns:
            Dict[str, Any]: {
                "success": bool,
                "message": str,
                "updated_fields": List[str]  # 实际更新的字段列表
            }
        """
        try:
            # 记录当前数据库会话状态
            logging.info(f"开始处理用户画像更新，用户ID: {user_id}, 事务状态: {db.is_active}")
            
            # 1. 获取当前用户画像
            query = select(UserProfileModel).filter(UserProfileModel.user_id == user_id)
            result = await db.execute(query)
            profile = result.scalar_one_or_none()
            
            if not profile:
                # 如果用户画像不存在，创建新的
                import uuid
                profile_id = str(uuid.uuid4())
                logging.info(f"为用户 {user_id} 创建新的用户画像，ID: {profile_id}")
                profile = UserProfileModel(id=profile_id, user_id=user_id)
                db.add(profile)
                logging.info(f"已将新用户画像添加到会话，用户ID: {user_id}")
            else:
                logging.info(f"找到现有用户画像，用户ID: {user_id}, 画像ID: {profile.id}")
            
            # 2. 记录实际更新的字段
            updated_fields = []
            update_reason = updates.pop("update_reason", "AI助手建议的更新")
            
            # 输出要更新的字段列表
            logging.info(f"要更新的字段列表: {list(updates.keys())}")
            
            # 3. 应用更新
            for field, value in updates.items():
                try:
                    if hasattr(profile, field):
                        old_value = getattr(profile, field)
                        # 检查值是否实际发生变化
                        if old_value != value:
                            logging.info(f"更新用户画像字段: {field}, 旧值: {old_value}, 新值: {value}")
                            setattr(profile, field, value)
                            updated_fields.append(field)
                        else:
                            logging.info(f"字段 {field} 值未变化，保持 {old_value}")
                    else:
                        logging.warning(f"用户画像模型没有字段: {field}，无法更新")
                except Exception as field_error:
                    logging.error(f"更新字段 {field} 失败: {str(field_error)}")
            
            if updated_fields:
                # 更新时间戳
                profile.updated_at = datetime.now()
                
                # 执行一次flush确保数据库更改可见
                await db.flush()
                
                # 记录日志但不提交，由调用者负责提交事务
                logging.info(
                    f"用户画像更新准备完成: user_id={user_id}, "
                    f"fields={updated_fields}, reason={update_reason}, "
                    f"当前事务状态: {db.is_active}"
                )
                
                return {
                    "success": True,
                    "message": "用户画像更新准备完成",
                    "updated_fields": updated_fields
                }
            else:
                logging.info(f"用户画像无需更新: user_id={user_id}, reason={update_reason}")
                return {
                    "success": True,
                    "message": "用户画像无需更新",
                    "updated_fields": []
                }
                
        except Exception as e:
            logging.error(f"处理用户画像更新失败: {e}")
            # 记录详细的错误堆栈
            import traceback
            logging.error(f"处理用户画像更新详细错误: {traceback.format_exc()}")
            # 由调用者负责处理回滚
            return {
                "success": False,
                "message": f"用户画像更新失败: {str(e)}",
                "updated_fields": []
            }