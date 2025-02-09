import gradio as gr
import json
from typing import List, Dict, Any, Union, AsyncGenerator
import base64
from io import BytesIO
import httpx
import os
from dotenv import load_dotenv
import numpy as np
from PIL import Image
import logging
from .services.ai_service_client import AIServiceClient
from .database import get_db
from .models.user import UserProfileModel
from sqlalchemy import select
from datetime import datetime

load_dotenv()
logger = logging.getLogger(__name__)

class GradioService:
    """Gradio服务类，提供AI服务接口"""
    
    def __init__(self):
        """初始化服务"""
        self.ai_client = AIServiceClient()
        self.chat_history = {}  # 用于存储每个会话的历史记录
        
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "qwen2.5:14b",
        max_tokens: int = 2000,
        user_profile: Dict[str, Any] = None
    ) -> str:
        """流式聊天接口"""
        try:
            async for chunk in self.ai_client.chat_stream(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                user_profile=user_profile
            ):
                yield chunk
            
        except Exception as e:
            logger.error(f"流式聊天请求失败: {e}")
            yield f"处理失败: {str(e)}"

    async def process_voice(self, audio_data: Union[str, bytes, tuple]) -> str:
        """处理语音转文字"""
        try:
            # 处理不同格式的音频输入
            if isinstance(audio_data, tuple):
                sample_rate, audio_array = audio_data
                # 将numpy数组转换为WAV格式
                import scipy.io.wavfile as wav
                audio_file = BytesIO()
                wav.write(audio_file, sample_rate, audio_array)
                audio_bytes = audio_file.getvalue()
            elif isinstance(audio_data, str):
                # 如果是文件路径，读取文件
                with open(audio_data, 'rb') as f:
                    audio_bytes = f.read()
            else:
                audio_bytes = audio_data
                
            # 调用真实的语音识别服务
            result = await self.ai_client.process_voice(audio_bytes)
            # 如果返回的是 bytes，则进行解码
            if isinstance(result, bytes):
                result = result.decode('utf-8', errors='replace')
            return result
            
        except Exception as e:
            logger.error(f"语音处理失败: {e}")
            return f"语音处理失败: {str(e)}"

    async def process_image(self, image_data: Union[str, bytes, np.ndarray], caption: str = "") -> Dict:
        """处理图片识别"""
        try:
            # 处理不同格式的图片输入
            if isinstance(image_data, str):
                # 如果是文件路径，直接传递
                image_path = image_data
            elif isinstance(image_data, np.ndarray):
                # 如果是numpy数组，保存为临时文件
                image = Image.fromarray(image_data)
                image_path = f"temp_{datetime.now().timestamp()}.jpg"
                image.save(image_path)
            else:
                # 如果是字节数据，保存为临时文件
                image = Image.open(BytesIO(image_data))
                image_path = f"temp_{datetime.now().timestamp()}.jpg"
                image.save(image_path)
                
            # 调用真实的图片识别服务
            result = await self.ai_client.recognize_food(image_path)
            
            # 如果是临时文件，清理它
            if isinstance(image_data, (np.ndarray, bytes)):
                os.remove(image_path)
                
            return result
            
        except Exception as e:
            logger.error(f"图片处理失败: {e}")
            return {
                "success": False,
                "message": f"图片处理失败: {str(e)}"
            }

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """获取用户画像"""
        try:
            # 使用 async for 来迭代获取 db 对象
            async for db in get_db():
                query = select(UserProfileModel).filter(UserProfileModel.user_id == user_id)
                result = await db.execute(query)
                profile = result.scalar_one_or_none()
                if not profile:
                    return {
                        "gender": "未知",
                        "age": None,
                        "height": None,
                        "weight": None,
                        "bmi": None,
                        "health_conditions": [],
                        "health_goals": [],
                        "food_preferences": [],
                        "dietary_restrictions": [],
                        "allergies": [],
                        "nutrition_goals": [],
                        "fitness_level": "初级",
                        "exercise_frequency": 0
                    }
                return {
                    "gender": profile.gender,
                    "age": (datetime.now().date() - profile.birth_date).days // 365 if profile.birth_date else None,
                    "height": profile.height,
                    "weight": profile.weight,
                    "bmi": round(profile.weight / ((profile.height/100) ** 2), 1) if profile.height and profile.weight else None,
                    "body_fat_percentage": profile.body_fat_percentage,
                    "health_conditions": profile.health_conditions or [],
                    "health_goals": profile.health_goals or [],
                    "food_preferences": profile.favorite_cuisines or [],
                    "dietary_restrictions": profile.dietary_restrictions or [],
                    "allergies": profile.allergies or [],
                    "cooking_level": profile.cooking_skill_level or "初级",
                    "nutrition_goals": profile.nutrition_goals or [],
                    "fitness_level": profile.fitness_level,
                    "exercise_frequency": profile.exercise_frequency,
                    "fitness_goals": profile.fitness_goals or []
                }
        except Exception as e:
            logger.error(f"获取用户画像失败: {e}")
            return {}

def create_interface():
    """创建Gradio界面"""
    service = GradioService()
    
    async def handle_text_message(message: str, history: List[Dict[str, str]]) -> AsyncGenerator[List[Dict[str, str]], None]:
        """处理文本消息，支持流式输出"""
        try:
            if not message:
                yield [{"role": "assistant", "content": "请输入消息"}]
                return
            
            # 获取用户画像
            user_profile = await service.get_user_profile("test_user")
            
            # 添加用户消息到历史
            history.append({"role": "user", "content": message})
            yield history
            
            # 处理消息并流式输出
            async for response_chunk in service.chat_stream(
                messages=history,
                model="qwen2.5:14b",
                user_profile=user_profile
            ):
                if response_chunk:
                    # 更新助手的最后一条消息
                    if len(history) > 0 and history[-1]["role"] == "assistant":
                        history[-1]["content"] += response_chunk
                    else:
                        history.append({"role": "assistant", "content": response_chunk})
                    yield history
                
        except Exception as e:
            logger.error(f"处理文本消息失败: {e}")
            history.append({"role": "assistant", "content": f"处理失败: {str(e)}"})
            yield history

    async def handle_voice_message(audio_data, history: List[Dict[str, str]]) -> AsyncGenerator[List[Dict[str, str]], None]:
        """处理语音消息，支持流式输出"""
        try:
            if audio_data is None:
                yield [{"role": "assistant", "content": "请先录制语音"}]
                return
            
            # 获取用户画像
            user_profile = await service.get_user_profile("test_user")
            
            # 语音转文字
            transcribed_text = await service.process_voice(audio_data)
            if not transcribed_text:
                yield [{"role": "assistant", "content": "语音识别失败"}]
                return
            
            # 先显示用户输入
            history = [{"role": "user", "content": f"语音输入：{transcribed_text}"}]
            yield history
            
            # 处理消息并流式输出
            async for response_chunk in service.chat_stream(
                messages=history,
                model="qwen2.5:14b",
                user_profile=user_profile
            ):
                if response_chunk:
                    # 更新助手的最后一条消息
                    if len(history) > 0 and history[-1]["role"] == "assistant":
                        history[-1]["content"] += response_chunk
                    else:
                        history.append({"role": "assistant", "content": response_chunk})
                    yield history
                
        except Exception as e:
            logger.error(f"处理语音消息失败: {e}")
            history.append({"role": "assistant", "content": f"处理失败: {str(e)}"})
            yield history

    async def handle_image_message(image, caption: str, history: List[Dict[str, str]]) -> AsyncGenerator[List[Dict[str, str]], None]:
        """处理图片消息，支持流式输出"""
        try:
            if image is None:
                yield [{"role": "assistant", "content": "请先上传图片"}]
                return
                
            # 显示处理中的状态
            history = [{"role": "user", "content": "图片上传成功"}]
            yield history
            
            history.append({"role": "assistant", "content": "正在识别图片中的食物..."})
            yield history
                
            # 图片识别
            recognition_result = await service.process_image(image, caption)
            if not recognition_result["success"]:
                history[-1]["content"] = f"图片识别失败: {recognition_result.get('message', '未知错误')}"
                yield history
                return
                
            # 构建消息
            food_items = recognition_result["food_items"]
            food_description = "图片中识别到的食物：" + ", ".join(
                [f"{item['name']}（置信度：{item['confidence']:.2%}）" 
                 for item in food_items]
            )
            
            # 更新识别结果
            history[-1]["content"] = food_description
            yield history
            
            # 如果有用户说明，添加到结果中
            if caption:
                history[-1]["content"] += f"\n用户说明：{caption}"
                yield history
                
        except Exception as e:
            logger.error(f"处理图片消息失败: {e}")
            yield [{"role": "assistant", "content": f"处理失败: {str(e)}"}]
    
    with gr.Blocks(title="Food Journey AI助手") as interface:
        gr.Markdown("""
        # Food Journey AI助手
        
        这是Food Journey AI助手的测试界面。你可以：
        1. 发送文本消息进行对话
        2. 发送语音进行对话（支持语音转文字）
        3. 上传图片进行对话（支持食物识别）
        """)
        
        with gr.Tab("文本聊天"):
            text_chatbot = gr.Chatbot(
                label="对话历史",
                height=400,
                type="messages",
                show_label=True,
                show_share_button=False,
                show_copy_button=True
            )
            with gr.Row():
                text_msg = gr.Textbox(
                    label="输入消息",
                    placeholder="请输入你的问题...",
                    lines=2
                )
                send_btn = gr.Button("发送")
            text_clear = gr.Button("清空对话")
            
            send_btn.click(
                handle_text_message,
                inputs=[text_msg, text_chatbot],
                outputs=text_chatbot
            ).then(
                lambda: "", None, text_msg  # 清空输入框
            )
            text_clear.click(lambda: None, None, text_chatbot, queue=False)
            
        with gr.Tab("语音聊天"):
            voice_chatbot = gr.Chatbot(
                label="对话历史",
                height=400,
                type="messages",
                show_label=True,
                show_share_button=False,
                show_copy_button=True
            )
            audio_msg = gr.Audio(
                label="录制语音",
                format="wav",
                sources=["microphone"]
            )
            voice_clear = gr.Button("清空对话")
            
            audio_msg.change(
                handle_voice_message,
                inputs=[audio_msg, voice_chatbot],
                outputs=voice_chatbot
            )
            voice_clear.click(lambda: None, None, voice_chatbot, queue=False)
            
        with gr.Tab("图片聊天"):
            image_chatbot = gr.Chatbot(
                label="对话历史",
                height=400,
                type="messages",
                show_label=True,
                show_share_button=False,
                show_copy_button=True
            )
            with gr.Row():
                image_input = gr.Image(
                    label="上传图片",
                    type="filepath"
                )
                caption_input = gr.Textbox(
                    label="补充说明",
                    placeholder="请输入图片补充说明（可选）",
                    lines=2
                )
            send_img_btn = gr.Button("发送")
            clear_img_btn = gr.Button("清空对话")

            send_img_btn.click(
                handle_image_message,
                inputs=[image_input, caption_input, image_chatbot],
                outputs=image_chatbot
            )
            clear_img_btn.click(lambda: None, None, image_chatbot, queue=False)
            
    return interface

def launch_interface():
    """启动Gradio界面"""
    interface = create_interface()
    interface.queue()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        debug=True
    )

if __name__ == "__main__":
    launch_interface() 