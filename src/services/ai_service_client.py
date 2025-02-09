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

load_dotenv()

class AIServiceClient:
    """AI服务客户端类
    
    负责与独立的AI服务进行通信，处理语音识别、LLM对话和图像识别请求
    """
    
    def __init__(self):
        """初始化AI服务客户端"""
        # 初始化各个服务的客户端
        self.chat_client = Client(os.getenv("CHAT_SERVICE_URL", "https://1ba902d825722a9416.gradio.live/"))
        self.voice_client = Client(os.getenv("VOICE_SERVICE_URL", "https://1ba902d825722a9416.gradio.live/"))
        self.food_client = Client(os.getenv("FOOD_SERVICE_URL", "https://1ba902d825722a9416.gradio.live/"))
        
        logging.info("AI服务客户端初始化成功")
        
    async def process_voice(self, audio_file: Union[str, BinaryIO, bytes]) -> str:
        """处理语音文件，转写为文本
        
        参数:
            audio_file: 音频文件路径或URL
        返回:
            str: 识别出的文本
        """
        try:
            # 如果是文件路径，转换为URL或处理本地文件
            if isinstance(audio_file, str):
                if audio_file.startswith("/uploads/voices/"):
                    # 将相对路径转换为完整URL
                    audio_url = f"{os.getenv('BASE_URL', 'http://localhost:8000')}{audio_file}"
                else:
                    audio_url = audio_file
                    
                # 调用语音识别服务
                result = self.voice_client.predict(
                    audio=handle_file(audio_url),
                    api_name="/voice_transcribe"
                )
                
                if isinstance(result, dict):
                    return result.get("text", "")
                return str(result)
                
            elif isinstance(audio_file, (bytes, BinaryIO)):
                # 如果是字节数据或文件对象，保存为临时文件
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    if isinstance(audio_file, bytes):
                        temp_file.write(audio_file)
                    else:
                        temp_file.write(audio_file.read())
                    temp_path = temp_file.name
                
                try:
                    # 使用临时文件路径调用语音识别服务
                    result = self.voice_client.predict(
                        audio=handle_file(temp_path),
                        api_name="/voice_transcribe"
                    )
                finally:
                    # 清理临时文件
                    os.unlink(temp_path)
                
                if isinstance(result, dict):
                    return result.get("text", "")
                return str(result)
            
            else:
                raise ValueError("不支持的音频输入类型")
                
        except Exception as e:
            logging.error(f"语音识别失败: {e}")
            raise
            
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

6. 用户画像更新：
   - 识别用户提供的新信息
   - 分析用户的行为变化
   - 及时更新相关建议

7. 非相关问题处理：
   - 礼貌地说明你只能回答与饮食、营养、运动、健康相关的问题
   - 不要给出任何非饮食、营养、运动、健康相关的问题的回答
   - 引导用户询问相关领域的问题
   - 如果问题部分相关，尽量从健康角度给出建议

请确保每次回复都体现专业性、针对性和全面性，帮助用户建立健康的生活方式。如果用户询问与饮食、营养、运动、健康无关的问题，请礼貌地说明你的专业范围并建议用户寻求相关领域的专家帮助。"""
        
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
            
            # 使用 predict 获取结果
            result = self.chat_client.predict(
                messages=full_messages,
                model=model,
                max_tokens=max_tokens,
                api_name="/chat_stream"
            )
            
            # 如果结果是生成器或迭代器，逐个产出结果
            if hasattr(result, '__iter__'):
                for chunk in result:
                    if chunk and isinstance(chunk, (str, dict)):
                        # 如果是字典，尝试获取文本内容
                        if isinstance(chunk, dict):
                            text = chunk.get("text", "") or chunk.get("content", "")
                        else:
                            text = chunk
                        
                        if text.strip():
                            yield text.strip()
            # 如果是单个结果，直接产出
            elif result:
                if isinstance(result, dict):
                    text = result.get("text", "") or result.get("content", "")
                else:
                    text = str(result)
                
                if text.strip():
                    yield text.strip()
                        
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