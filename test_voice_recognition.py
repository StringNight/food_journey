import os
import logging
import asyncio
import sys
from dotenv import load_dotenv
from gradio_client import Client
from pathlib import Path
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def test_remote_api():
    """测试远程语音识别API"""
    try:
        # 获取远程服务URL
        load_dotenv()
        service_url = os.getenv("VOICE_SERVICE_URL", "https://gradio-food-journey.hf.space")
        logger.info(f"连接远程语音服务: {service_url}")
        
        # 创建客户端
        client = Client(service_url)
        logger.info(f"连接成功")
        
        # 获取可用API
        endpoints = client.endpoints
        logger.info(f"可用API端点: {endpoints}")
        
        # 查找语音识别相关API
        voice_apis = [api for api in endpoints if "voice" in api.lower() or "transcribe" in api.lower() or "audio" in api.lower() or "speech" in api.lower()]
        if voice_apis:
            logger.info(f"找到语音相关API: {voice_apis}")
        else:
            logger.warning(f"未找到语音相关API，将使用默认API '/voice_transcribe'")
        
        # 查找测试用的音频文件
        voices_dir = os.path.join(os.getcwd(), "uploads", "voices")
        if not os.path.exists(voices_dir):
            logger.error(f"语音目录不存在: {voices_dir}")
            return
            
        audio_files = [f for f in os.listdir(voices_dir) if f.endswith((".wav", ".mp3", ".m4a"))]
        if not audio_files:
            logger.error("没有找到测试音频文件")
            return
            
        test_file = os.path.join(voices_dir, audio_files[0])
        logger.info(f"使用测试文件: {test_file}")
        
        # 测试API
        result = None
        api_used = None
        
        # 先尝试找到的语音API
        for api in voice_apis:
            try:
                logger.info(f"尝试API: {api}")
                result = client.predict(audio=test_file, api_name=api)
                logger.info(f"调用成功! 结果: {result}")
                api_used = api
                break
            except Exception as e:
                logger.error(f"API {api} 调用失败: {e}")
                
        # 如果找不到合适的API，尝试默认API
        if result is None:
            try:
                logger.info("尝试默认API '/voice_transcribe'")
                result = client.predict(audio=test_file, api_name="/voice_transcribe")
                logger.info(f"默认API调用成功! 结果: {result}")
                api_used = "/voice_transcribe"
            except Exception as e:
                logger.error(f"默认API调用失败: {e}")
                
        # 如果所有尝试都失败，输出详细信息
        if result is None:
            logger.error("所有API调用尝试均失败")
            # 检查文件格式
            import mimetypes
            mime_type = mimetypes.guess_type(test_file)[0]
            logger.info(f"测试文件MIME类型: {mime_type}")
            logger.info(f"测试文件大小: {os.path.getsize(test_file)} bytes")
            return
            
        # 记录成功的API
        logger.info(f"成功的API: {api_used}")
        logger.info(f"结果类型: {type(result)}")
        
        # 将结果写入环境变量文件
        with open(".env", "a") as f:
            f.write(f"\n# 测试发现的有效语音API\nVOICE_API_ENDPOINT={api_used}\n")
        logger.info(f"已将成功的API端点写入.env文件")
            
    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_remote_api()) 