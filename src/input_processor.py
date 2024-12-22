from .voice_processor import VoiceProcessor
from .image_processor import ImageProcessor
import logging

class InputProcessor:
    def __init__(self):
        try:
            self.voice_processor = VoiceProcessor()
            self.image_processor = ImageProcessor()
        except Exception as e:
            logging.error(f"输入处理器初始化失败: {e}")
            raise
    
    def process_voice(self, audio_file) -> str:
        return self.voice_processor.process_voice(audio_file)
    
    def process_image(self, image_file) -> list[str]:
        return self.image_processor.process_image(image_file)