import httpx
import logging
from typing import Optional, Dict, List, Union, BinaryIO, Any
import os
from dotenv import load_dotenv
from gradio_client import Client

load_dotenv()

class AIServiceClient:
    """AI服务客户端类
    
    负责与独立的AI服务进行通信，处理语音识别、LLM对话和图像识别请求
    """
    
    def __init__(self):
        """初始化AI服务客户端"""
        from gradio_client import Client
        
        # 初始化各个服务的客户端
        self.chat_client = Client("https://63e9cf37a8d05f9e2b.gradio.live/")
        self.chat_stream_client = Client("https://63e9cf37a8d05f9e2b.gradio.live/")
        self.voice_client = Client("https://63e9cf37a8d05f9e2b.gradio.live/")
        self.food_client = Client("https://63e9cf37a8d05f9e2b.gradio.live/")
        
        logging.info("AI服务客户端初始化成功")
        
    async def process_voice(self, audio_file: Union[str, BinaryIO, bytes]) -> str:
        """
        处理语音文件，转写为文本
        
        Args:
            audio_file: 音频文件数据
            
        Returns:
            str: 识别出的文本
        """
        try:
            from gradio_client import handle_file
            result = self.voice_client.predict(
                audio=handle_file(audio_file),  # 使用 handle_file 处理音频文件
                api_name="/voice_transcribe"
            )
            return result
            
        except Exception as e:
            logging.error(f"语音处理请求失败: {e}")
            raise
            
    async def chat(self, messages: List[Dict[str, str]], model: str = "qwen2.5:14b", max_tokens: int = 2000) -> Dict:
        """
        发送聊天请求
        
        Args:
            messages: 消息历史
            model: 模型名称
            max_tokens: 最大token数
            
        Returns:
            Dict: 包含响应内容的字典
        """
        try:
            result = self.chat_client.predict(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                api_name="/chat"
            )
            
            return {
                "response": result
            }
            
        except Exception as e:
            logging.error(f"聊天请求失败: {e}")
            raise
            
    async def chat_stream(self, messages: List[Dict[str, str]], model: str = "qwen2.5:14b", max_tokens: int = 2000):
        """
        发送流式聊天请求
        
        Args:
            messages: 消息历史
            model: 模型名称
            max_tokens: 最大token数
            
        Returns:
            AsyncGenerator: 生成响应流
        """
        try:
            result = self.chat_stream_client.predict(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                api_name="/chat_stream"
            )
            
            # 处理流式响应
            for chunk in result:
                if chunk:
                    yield chunk
                        
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
            # 记录输入数据类型
            logging.info(f"接收到的图片数据类型: {type(image_data)}")
            
            # 1. 首先获取图片的二进制数据
            if isinstance(image_data, str):
                # 如果是文件路径，读取文件内容
                logging.info(f"从文件路径读取图片: {image_data}")
                with open(image_data, 'rb') as f:
                    image_bytes = f.read()
            elif isinstance(image_data, BinaryIO):
                # 如果是文件对象，读取内容
                logging.info(f"从文件对象读取图片: {image_data.name if hasattr(image_data, 'name') else 'unknown'}")
                image_bytes = image_data.read()
            else:
                # 如果是字节数据，直接使用
                logging.info("使用直接传入的字节数据")
                image_bytes = image_data
            
            # 检查图片大小
            image_size = len(image_bytes)
            logging.info(f"原始图片大小: {image_size} bytes")
            
            # 如果图片太大，进行压缩
            if image_size > 1024 * 1024:  # 如果大于1MB
                from PIL import Image
                import io
                
                # 使用PIL打开图片
                image = Image.open(io.BytesIO(image_bytes))
                
                # 计算新的尺寸，保持宽高比
                max_size = 800  # 降低最大边长到800像素
                ratio = min(max_size / image.width, max_size / image.height)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                
                # 调整图片大小
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                
                # 保存为JPEG格式，降低质量
                output = io.BytesIO()
                image.save(output, format='JPEG', quality=75)  # 降低质量到75
                image_bytes = output.getvalue()
                logging.info(f"压缩后的图片大小: {len(image_bytes)} bytes")
            
            # 2. 将图片转换为纯base64字符串
            import base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            logging.info(f"转换后的base64字符串长度: {len(image_base64)}")
            logging.info(f"base64字符串前100个字符: {image_base64[:100]}")
            
            # 3. 发送预测请求
            logging.info("开始发送预测请求...")
            result = self.food_client.predict(
                file=image_base64,  # 使用关键字参数传递base64字符串
                api_name="/food_recognition"
            )
            logging.info(f"收到预测结果: {result}")
            
            # 4. 处理返回结果
            if not result:
                logging.warning("识别服务返回空结果")
                return {
                    "success": False,
                    "message": "识别服务未返回结果"
                }
            
            return {
                "success": True,
                "food_items": [{"name": result, "confidence": 1.0}]
            }
            
        except Exception as e:
            logging.error(f"食物识别请求失败: {e}", exc_info=True)
            # 提供更详细的错误信息
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