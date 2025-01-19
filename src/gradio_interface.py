import gradio as gr
import json
from typing import List, Dict
import base64
from io import BytesIO
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

# 配置
AI_SERVICE_URL = os.getenv('AI_SERVICE_URL', 'https://97c0a4fd9fb39fb02d.gradio.live')
API_KEY = os.getenv('AI_SERVICE_API_KEY')

# 创建HTTP客户端
client = httpx.AsyncClient(
    base_url=AI_SERVICE_URL,
    headers={
        "Authorization": f"Bearer {API_KEY}"
    },
    timeout=60.0
)

async def chat(
    messages: List[Dict[str, str]],
    model: str = "qwen2.5:14b",
    max_tokens: int = 2000
) -> str:
    """发送聊天请求"""
    try:
        data = {
            "messages": messages,
            "model": model,
            "max_tokens": max_tokens
        }
        
        response = await client.post("/chat", json=data)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")
        
    except Exception as e:
        return f"聊天请求失败: {str(e)}"

async def chat_stream(
    messages: List[Dict[str, str]],
    model: str = "qwen2.5:14b",
    max_tokens: int = 2000
):
    """发送流式聊天请求"""
    try:
        data = {
            "messages": messages,
            "model": model,
            "max_tokens": max_tokens
        }
        
        async with client.stream("POST", "/chat_stream", json=data) as response:
            response.raise_for_status()
            async for chunk in response.aiter_lines():
                if chunk:
                    yield chunk
                    
    except Exception as e:
        yield f"流式聊天请求失败: {str(e)}"

async def process_voice(audio_data) -> str:
    """处理语音文件"""
    try:
        # 将音频数据转换为文件格式
        if isinstance(audio_data, tuple):
            sample_rate, audio_array = audio_data
            audio_file = BytesIO()
            # 保存为WAV格式
            import scipy.io.wavfile as wav
            wav.write(audio_file, sample_rate, audio_array)
            audio_file.seek(0)
            files = {"audio": ("audio.wav", audio_file, "audio/wav")}
        else:
            files = {"audio": ("audio.wav", audio_data, "audio/wav")}
            
        response = await client.post("/voice_transcribe", files=files)
        response.raise_for_status()
        
        result = response.json()
        return result.get("text", "")
        
    except Exception as e:
        return f"语音处理失败: {str(e)}"

async def recognize_food(image) -> str:
    """识别食物图片"""
    try:
        # 将图片转换为base64
        if isinstance(image, str):
            with open(image, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
        else:
            image_data = base64.b64encode(image).decode('utf-8')
            
        data = {"file": image_data}
        response = await client.post("/food_recognition", json=data)
        response.raise_for_status()
        
        result = response.json()
        if not result.get("success", False):
            return result.get("message", "食物识别失败")
            
        # 格式化识别结果
        food_items = result.get("food_items", [])
        if not food_items:
            return "未识别到食物"
            
        output = "识别到以下食物：\n"
        for item in food_items:
            name = item.get("name", "未知食物")
            confidence = item.get("confidence", 0)
            output += f"- {name} (置信度: {confidence:.2%})\n"
            
        return output
        
    except Exception as e:
        return f"食物识别失败: {str(e)}"

async def text_chat(message: str, history: List[List[str]]) -> str:
    """处理文本聊天"""
    try:
        # 转换历史记录格式
        messages = []
        for human, assistant in history:
            messages.append({"role": "user", "content": human})
            messages.append({"role": "assistant", "content": assistant})
            
        # 添加当前消息
        messages.append({"role": "user", "content": message})
        
        # 发送请求
        response = await chat(messages)
        return response
        
    except Exception as e:
        return f"处理失败: {str(e)}"

async def voice_chat(audio_data, history: List[List[str]]) -> str:
    """处理语音聊天"""
    try:
        # 首先转写语音
        transcribed_text = await process_voice(audio_data)
        if transcribed_text.startswith("语音处理失败"):
            return transcribed_text
            
        # 转换历史记录格式
        messages = []
        for human, assistant in history:
            messages.append({"role": "user", "content": human})
            messages.append({"role": "assistant", "content": assistant})
            
        # 添加转写的文本
        messages.append({"role": "user", "content": transcribed_text})
        
        # 发送聊天请求
        response = await chat(messages)
        return f"语音转写：{transcribed_text}\n\n助手回复：{response}"
        
    except Exception as e:
        return f"处理失败: {str(e)}"

async def image_chat(image, history: List[List[str]]) -> str:
    """处理图片聊天"""
    try:
        # 首先识别食物
        recognition_result = await recognize_food(image)
        if recognition_result.startswith("食物识别失败"):
            return recognition_result
            
        # 转换历史记录格式
        messages = []
        for human, assistant in history:
            messages.append({"role": "user", "content": human})
            messages.append({"role": "assistant", "content": assistant})
            
        # 添加识别结果
        prompt = f"请根据以下食物识别结果，给出营养建议和食谱推荐：\n\n{recognition_result}"
        messages.append({"role": "user", "content": prompt})
        
        # 发送聊天请求
        response = await chat(messages)
        return f"{recognition_result}\n\n助手建议：{response}"
        
    except Exception as e:
        return f"处理失败: {str(e)}"

def create_interface():
    """创建Gradio界面"""
    
    with gr.Blocks(title="Food Journey AI助手") as interface:
        gr.Markdown("""
        # Food Journey AI助手
        
        这是一个用于测试Food Journey AI功能的界面。你可以：
        1. 发送文本消息进行对话
        2. 发送语音进行对话（支持语音转文字）
        3. 上传食物图片进行识别和分析
        """)
        
        with gr.Tab("文本聊天"):
            text_chatbot = gr.Chatbot(
                label="对话历史",
                height=400
            )
            text_msg = gr.Textbox(
                label="输入消息",
                placeholder="请输入你的问题...",
                lines=2
            )
            text_clear = gr.Button("清空对话")
            
            text_msg.submit(
                text_chat,
                [text_msg, text_chatbot],
                [text_chatbot],
                clear_input=True
            )
            text_clear.click(lambda: None, None, text_chatbot, queue=False)
            
        with gr.Tab("语音聊天"):
            voice_chatbot = gr.Chatbot(
                label="对话历史",
                height=400
            )
            audio_msg = gr.Audio(
                label="录制语音",
                source="microphone",
                type="filepath"
            )
            voice_clear = gr.Button("清空对话")
            
            audio_msg.change(
                voice_chat,
                [audio_msg, voice_chatbot],
                [voice_chatbot]
            )
            voice_clear.click(lambda: None, None, voice_chatbot, queue=False)
            
        with gr.Tab("食物识别"):
            image_chatbot = gr.Chatbot(
                label="对话历史",
                height=400
            )
            with gr.Row():
                with gr.Column():
                    image_input = gr.Image(
                        label="上传食物图片",
                        type="filepath"
                    )
                with gr.Column():
                    image_output = gr.Textbox(
                        label="识别结果",
                        lines=10,
                        readonly=True
                    )
            image_clear = gr.Button("清空记录")
            
            image_input.change(
                image_chat,
                [image_input, image_chatbot],
                [image_chatbot]
            )
            image_clear.click(lambda: None, None, image_chatbot, queue=False)
            
    return interface 