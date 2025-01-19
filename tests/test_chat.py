"""聊天功能测试"""

import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
import os
import logging
from datetime import datetime, timedelta
import asyncio
import math

logger = logging.getLogger(__name__)

@pytest.fixture
def mock_ai_service():
    """模拟AI服务的响应"""
    with patch("src.routers.chat.ai_client") as mock_client:
        # 模拟文本聊天响应
        mock_client.chat = AsyncMock(return_value={
            "content": "这是一个测试回复",
            "suggestions": ["建议1", "建议2"]
        })
        
        # 模拟语音转文本响应
        mock_client.transcribe_audio = AsyncMock(return_value="这是语音转文本的结果")
        
        # 模拟图片分析响应
        mock_client.analyze_image = AsyncMock(return_value="我看到了一个苹果,置信度95%")
        
        yield mock_client

@pytest.mark.asyncio
async def test_text_chat(test_client: AsyncClient, mock_ai_service, test_user_token: str):
    """测试文本聊天功能"""
    response = await test_client.post(
        "/api/v1/chat/text",
        json={"message": "你好"},
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["schema_version"] == "1.0"
    assert data["message"] == "这是一个测试回复"
    assert data["suggestions"] == ["建议1", "建议2"]
    
    # 验证AI服务调用
    mock_ai_service.chat.assert_called_once()

@pytest.mark.asyncio
async def test_voice_chat(test_client: AsyncClient, mock_ai_service, test_user_token: str):
    """测试语音聊天功能"""
    # 创建一个完整的WAV文件
    wav_header = bytearray([
        # RIFF header
        0x52, 0x49, 0x46, 0x46,  # "RIFF"
        0x24, 0x00, 0x00, 0x00,  # Chunk size (36 bytes)
        0x57, 0x41, 0x56, 0x45,  # "WAVE"
        
        # fmt chunk
        0x66, 0x6D, 0x74, 0x20,  # "fmt "
        0x10, 0x00, 0x00, 0x00,  # Chunk size (16 bytes)
        0x01, 0x00,              # Audio format (PCM)
        0x01, 0x00,              # Channels (1)
        0x44, 0xAC, 0x00, 0x00,  # Sample rate (44100 Hz)
        0x88, 0x58, 0x01, 0x00,  # Byte rate (44100 * 1 * 2)
        0x02, 0x00,              # Block align
        0x10, 0x00,              # Bits per sample (16)
        
        # data chunk
        0x64, 0x61, 0x74, 0x61,  # "data"
        0x00, 0x00, 0x00, 0x00   # Chunk size (0 bytes)
    ])
    
    # 添加一些实际的音频数据（1秒的44.1kHz, 16位单声道音频）
    audio_data = bytearray()
    for i in range(44100):  # 1秒的采样
        # 生成一个440Hz的正弦波
        t = i / 44100.0
        value = int(32767 * 0.5 * math.sin(2 * math.pi * 440 * t))
        # 使用小端字节序(little-endian)写入16位有符号整数
        audio_data.extend(value.to_bytes(2, byteorder='little', signed=True))
    
    # 更新文件大小
    file_size = len(audio_data) + 36  # 36是头部大小
    wav_header[4:8] = file_size.to_bytes(4, byteorder='little')
    
    # 更新数据块大小
    data_size = len(audio_data)
    wav_header[-4:] = data_size.to_bytes(4, byteorder='little')
    
    # 组合完整的WAV文件
    test_audio = bytes(wav_header) + bytes(audio_data)
    
    response = await test_client.post(
        "/api/v1/chat/voice",
        files={"file": ("test.wav", test_audio, "audio/wav")},
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["schema_version"] == "1.0"
    assert data["message"] == "这是一个测试回复"
    assert data["transcribed_text"] == "这是语音转文本的结果"
    assert data["voice_url"].startswith("/uploads/voices/")
    
    # 验证AI服务调用
    mock_ai_service.transcribe_audio.assert_called_once()
    mock_ai_service.chat.assert_called_once()

@pytest.mark.asyncio
async def test_image_chat(test_client: AsyncClient, mock_ai_service, test_user_token: str):
    """测试图片聊天功能"""
    # 创建一个最小但有效的JPEG文件
    jpeg_data = bytes([
        # SOI marker
        0xFF, 0xD8,
        
        # APP0 segment
        0xFF, 0xE0,                    # APP0 marker
        0x00, 0x10,                    # Length (16 bytes)
        0x4A, 0x46, 0x49, 0x46, 0x00, # "JFIF\0"
        0x01, 0x01,                    # Version 1.1
        0x00,                          # Units: none
        0x00, 0x01,                    # X density (1)
        0x00, 0x01,                    # Y density (1)
        0x00, 0x00,                    # Thumbnail (none)
        
        # DQT segment - Luminance
        0xFF, 0xDB,                    # DQT marker
        0x00, 0x43,                    # Length (67 bytes)
        0x00,                          # Table ID
        # Standard JPEG luminance quantization table
        0x10, 0x0B, 0x0C, 0x0E, 0x0C, 0x0A, 0x10, 0x0E,
        0x0D, 0x0E, 0x12, 0x11, 0x10, 0x13, 0x18, 0x28,
        0x1A, 0x18, 0x16, 0x16, 0x18, 0x31, 0x23, 0x25,
        0x1D, 0x28, 0x3A, 0x33, 0x3D, 0x3C, 0x39, 0x33,
        0x38, 0x37, 0x40, 0x48, 0x5C, 0x4E, 0x40, 0x44,
        0x57, 0x45, 0x37, 0x38, 0x50, 0x6D, 0x51, 0x57,
        0x5F, 0x62, 0x67, 0x68, 0x67, 0x3E, 0x4D, 0x71,
        0x79, 0x70, 0x64, 0x78, 0x5C, 0x65, 0x67, 0x63,
        
        # SOF0 segment
        0xFF, 0xC0,                    # SOF0 marker
        0x00, 0x11,                    # Length (17 bytes)
        0x08,                          # Precision (8 bits)
        0x00, 0x08,                    # Height (8 pixels)
        0x00, 0x08,                    # Width (8 pixels)
        0x01,                          # Number of components
        0x01, 0x11, 0x00,             # Component data
        
        # DHT segment - DC Luminance
        0xFF, 0xC4,                    # DHT marker
        0x00, 0x1F,                    # Length (31 bytes)
        0x00,                          # Table class and ID
        # Standard DC luminance bit lengths
        0x00, 0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01,
        0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        # Standard DC luminance values
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
        0x08, 0x09, 0x0A, 0x0B,
        
        # DHT segment - AC Luminance
        0xFF, 0xC4,                    # DHT marker
        0x00, 0xB5,                    # Length (181 bytes)
        0x10,                          # Table class and ID
        # Standard AC luminance bit lengths
        0x00, 0x02, 0x01, 0x03, 0x03, 0x02, 0x04, 0x03,
        0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
        # Standard AC luminance values
        0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12,
        0x21, 0x31, 0x41, 0x06, 0x13, 0x51, 0x61, 0x07,
        0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
        0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0,
        0x24, 0x33, 0x62, 0x72, 0x82, 0x09, 0x0A, 0x16,
        0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
        0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39,
        0x3A, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49,
        0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
        0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69,
        0x6A, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79,
        0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
        0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98,
        0x99, 0x9A, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7,
        0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
        0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5,
        0xC6, 0xC7, 0xC8, 0xC9, 0xCA, 0xD2, 0xD3, 0xD4,
        0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
        0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA,
        0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7, 0xF8,
        0xF9, 0xFA,
        
        # SOS segment
        0xFF, 0xDA,                    # SOS marker
        0x00, 0x08,                    # Length (8 bytes)
        0x01,                          # Number of components
        0x01, 0x00,                    # Component data
        0x00, 0x3F, 0x00,             # Other parameters
        
        # Minimal image data (8x8 pixels, all black)
        0x00, 0xFF,                    # DC coefficient
        0x00, 0x00, 0x00, 0x00,       # AC coefficients (RLE encoded)
        
        # EOI marker
        0xFF, 0xD9
    ])
    
    response = await test_client.post(
        "/api/v1/chat/image",
        files={"file": ("test.jpg", jpeg_data, "image/jpeg")},
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["schema_version"] == "1.0"
    assert data["message"] == "这是一个测试回复"
    assert data["image_url"].startswith("/uploads/images/")
    assert data["analysis_result"] == "我看到了一个苹果,置信度95%"
    
    # 验证AI服务调用
    mock_ai_service.analyze_image.assert_called_once()
    mock_ai_service.chat.assert_called_once()

@pytest.mark.asyncio
async def test_chat_history(test_client: AsyncClient, mock_ai_service, test_user_token: str):
    """测试聊天历史记录"""
    # 先发送一条消息
    await test_client.post(
        "/api/v1/chat/text",
        json={"message": "测试消息"},
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    # 获取历史记录
    response = await test_client.get(
        "/api/v1/chat/history",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["schema_version"] == "1.0"
    assert len(data["messages"]) > 0
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["per_page"] == 20

@pytest.mark.asyncio
async def test_invalid_voice_format(test_client: AsyncClient, test_user_token: str):
    """测试无效的语音格式"""
    test_audio = b"test audio content"
    response = await test_client.post(
        "/api/v1/chat/voice",
        files={"file": ("test.txt", test_audio, "text/plain")},
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 400
    assert "不支持的音频格式" in response.json()["detail"]

@pytest.mark.asyncio
async def test_invalid_image_format(test_client: AsyncClient, test_user_token: str):
    """测试无效的图片格式"""
    test_image = b"test image content"
    response = await test_client.post(
        "/api/v1/chat/image",
        files={"file": ("test.txt", test_image, "text/plain")},
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 400
    assert "不支持的图片格式" in response.json()["detail"]

@pytest.mark.asyncio
async def test_chat_history_pagination(test_client: AsyncClient, mock_ai_service, test_user_token: str):
    """测试聊天历史记录分页"""
    # 发送多条消息
    for i in range(25):
        await test_client.post(
            "/api/v1/chat/text",
            json={"message": f"测试消息 {i}"},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
    
    # 获取第二页
    response = await test_client.get(
        "/api/v1/chat/history?page=2&per_page=10",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["page"] == 2
    assert data["pagination"]["per_page"] == 10
    assert len(data["messages"]) == 10

@pytest.mark.asyncio
async def test_chat_history_date_filter(test_client: AsyncClient, mock_ai_service, test_user_token: str):
    """测试聊天历史记录日期过滤"""
    # 获取带日期过滤的历史记录
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    
    response = await test_client.get(
        f"/api/v1/chat/history?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["schema_version"] == "1.0"
    
    # 验证所有消息的创建时间在指定范围内
    for message in data["messages"]:
        created_at = datetime.fromisoformat(message["created_at"])
        assert start_date <= created_at <= end_date 

@pytest.mark.asyncio
async def test_long_text_chat(test_client: AsyncClient, mock_ai_service, test_user_token: str):
    """测试超长文本聊天"""
    try:
        # 创建一个超长的消息（例如10000个字符）
        long_message = "测试" * 2500  # 10000个字符
        
        response = await test_client.post(
            "/api/v1/chat/text",
            json={"message": long_message},
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        
        # 验证响应
        assert response.status_code == 413  # Request Entity Too Large
        
        logger.info("Long text chat test successful")
        
    except Exception as e:
        logger.error(f"Error in test_long_text_chat: {e}")
        raise

@pytest.mark.asyncio
async def test_special_characters_chat(test_client: AsyncClient, mock_ai_service, test_user_token: str):
    """测试包含特殊字符的聊天"""
    try:
        # 包含HTML标签、SQL注入和JS脚本的消息
        special_messages = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "<img src='x' onerror='alert(1)'>",
            "{{7*7}}",
            "${7*7}",
            "/* */; SELECT * FROM recipes;"
        ]
        
        for message in special_messages:
            response = await test_client.post(
                "/api/v1/chat/text",
                json={"message": message},
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            
            # 验证响应
            assert response.status_code == 200
            data = response.json()
            # 确保返回的消息被正确转义或过滤
            assert "<script>" not in data["message"]
            assert "alert" not in data["message"]
            
        logger.info("Special characters chat test successful")
        
    except Exception as e:
        logger.error(f"Error in test_special_characters_chat: {e}")
        raise

@pytest.mark.asyncio
async def test_concurrent_chat(test_client: AsyncClient, mock_ai_service, test_user_token: str):
    """测试并发聊天请求"""
    try:
        # 创建多个并发请求
        async def make_request():
            return await test_client.post(
                "/api/v1/chat/text",
                json={"message": "并发测试消息"},
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
        
        # 同时发送10个请求
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # 验证所有响应
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "suggestions" in data
        
        logger.info("Concurrent chat test successful")
        
    except Exception as e:
        logger.error(f"Error in test_concurrent_chat: {e}")
        raise

@pytest.mark.asyncio
async def test_empty_message(test_client: AsyncClient, mock_ai_service, test_user_token: str):
    """测试空消息和仅包含空白字符的消息"""
    try:
        test_cases = [
            "",
            " ",
            "\n",
            "\t",
            "   \n   \t   "
        ]
        
        for message in test_cases:
            response = await test_client.post(
                "/api/v1/chat/text",
                json={"message": message},
                headers={"Authorization": f"Bearer {test_user_token}"}
            )
            
            # 验证响应
            assert response.status_code == 400
            assert "消息不能为空" in response.json()["detail"]
        
        logger.info("Empty message test successful")
        
    except Exception as e:
        logger.error(f"Error in test_empty_message: {e}")
        raise 