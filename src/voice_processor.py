import logging
import wenet
import torchaudio
import os

class VoiceProcessor:
    def __init__(self):
        try:
            # 初始化 WeNet 模型
            self.model = wenet.load_model('chinese')
            logging.info("WeNet 语音处理器初始化成功")
        except Exception as e:
            logging.error(f"WeNet 模型加载失败: {e}")
            raise

    def process_voice(self, audio_file: str) -> str:
        """
        处理语音文件并返回识别文本。
        
        参数:
            audio_file (str): 音频文件路径。

        返回:
            str: 转录的文本。
        """
        try:
            # 加载音频文件
            if not os.path.exists(audio_file):
                raise FileNotFoundError(f"音频文件未找到: {audio_file}")
            
            logging.info(f"加载音频文件: {audio_file}")
            waveform, sample_rate = torchaudio.load(audio_file)
            
            # 确保采样率为 16kHz
            if sample_rate != 16000:
                logging.info("重采样音频到 16kHz")
                resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                waveform = resampler(waveform)
                sample_rate = 16000
            
            # 转换为单声道（如有必要）
            if waveform.shape[0] > 1:
                logging.info("将多声道音频转换为单声道")
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # 保存临时音频文件
            temp_audio_file = "temp_audio.wav"
            torchaudio.save(temp_audio_file, waveform, sample_rate)
            
            # 使用 WeNet 模型进行转录
            logging.info("开始语音转录")
            result = self.model.transcribe(temp_audio_file)
            os.remove(temp_audio_file)  # 删除临时文件
            
            logging.info(f"转录结果: {result['text']}")
            return result['text']
        
        except Exception as e:
            logging.error(f"语音处理失败: {e}")
            return "无法识别语音内容"