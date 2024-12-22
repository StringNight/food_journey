import whisper
import logging
import torch

class VoiceProcessor:
    def __init__(self):
        try:
            # 强制使用 CPU 设备
            self.device = "cpu"
            logging.info(f"使用 {self.device} 设备进行语音处理")
            
            # 加载模型时指定设备
            self.model = whisper.load_model(
                "base",
                device=self.device
            )
        except Exception as e:
            logging.error(f"语音处理器初始化失败: {e}")
            raise
    
    def process_voice(self, audio_file) -> str:
        try:
            result = self.model.transcribe(audio_file, language="zh", fp16=False)
            return result['text']
        except Exception as e:
            logging.error(f"语音处理失败: {e}")
            return "无法识别语音内容" 