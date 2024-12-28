import logging
import torch
import torchaudio
import os
import tempfile
from pathlib import Path
from typing import Tuple, Optional, Union, BinaryIO
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

class VoiceProcessor:
    def __init__(self):
        try:
            # 初始化 wav2vec2.0 模型和处理器
            model_name = "jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn"
            
            # 使用缓存加载模型
            cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "voice_models")
            os.makedirs(cache_dir, exist_ok=True)
            
            logging.info("正在加载语音识别模型...")
            self.processor = Wav2Vec2Processor.from_pretrained(
                model_name,
                cache_dir=cache_dir
            )
            self.model = Wav2Vec2ForCTC.from_pretrained(
                model_name,
                cache_dir=cache_dir,
                ignore_mismatched_sizes=True
            )
            
            # 设置设备并移动模型
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            self.model.eval()  # 设置为评估模式
            
            logging.info(f"Wav2Vec2.0 语音处理器初始化成功，使用设备: {self.device}")
        except Exception as e:
            logging.error(f"Wav2Vec2.0 模型加载失败: {e}")
            raise

    def _save_upload_file(self, file: Union[str, BinaryIO, bytes]) -> str:
        """
        保存上传的文件到临时目录。
        
        参数:
            file: 可以是文件路径、文件对象或字节数据
            
        返回:
            str: 临时文件的路径
        """
        try:
            # 创建临时文件
            temp_dir = os.path.join(tempfile.gettempdir(), "voice_processor")
            os.makedirs(temp_dir, exist_ok=True)
            
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".wav",
                dir=temp_dir
            )
            
            # 处理不同类型的输入
            if isinstance(file, str):
                if os.path.exists(file):
                    with open(file, 'rb') as f:
                        temp_file.write(f.read())
            elif isinstance(file, bytes):
                temp_file.write(file)
            else:  # 文件对象
                temp_file.write(file.read())
            
            temp_file.close()
            return temp_file.name
            
        except Exception as e:
            logging.error(f"保存上传文件失败: {e}")
            raise

    def _load_and_prepare_audio(self, audio_file: str) -> Tuple[torch.Tensor, int]:
        """
        加载并预处理音频文件。
        
        参数:
            audio_file (str): 音频文件路径
            
        返回:
            Tuple[torch.Tensor, int]: 处理后的波形和采样率
        """
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
        
        # 转换为单声道
        if waveform.shape[0] > 1:
            logging.info("将多声道音频转换为单声道")
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        
        return waveform, sample_rate

    def process_voice(self, file: Union[str, BinaryIO, bytes]) -> str:
        """
        处理语音文件并返回识别文本。
        
        参数:
            file: 可以是文件路径、文件对象或字节数据

        返回:
            str: 转录的文本。
        """
        temp_file = None
        try:
            # 如果不是字符串路径，保存为临时文件
            if not isinstance(file, str) or not os.path.exists(file):
                temp_file = self._save_upload_file(file)
                audio_file = temp_file
            else:
                audio_file = file
            
            # 加载和预处理音频
            waveform, _ = self._load_and_prepare_audio(audio_file)
            
            # 准备输入数据
            waveform = waveform.squeeze().numpy()
            inputs = self.processor(
                waveform, 
                sampling_rate=16000, 
                return_tensors="pt", 
                padding=True
            )
            
            # 移动数据到正确的设备
            input_values = inputs.input_values.to(self.device)
            
            # 使用模型进行预测
            logging.info("开始语音转录")
            with torch.no_grad():
                logits = self.model(input_values).logits
                predicted_ids = torch.argmax(logits, dim=-1)
                transcription = self.processor.batch_decode(predicted_ids)[0]
            
            logging.info(f"转录结果: {transcription}")
            return transcription
        
        except Exception as e:
            logging.error(f"语音处理失败: {e}")
            return "无法识别语音内容"
        finally:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logging.warning(f"清理临时文件失败: {e}")

    def __del__(self):
        """析构函数，确保资源被正确释放"""
        try:
            # 清理 CUDA 内存
            if hasattr(self, 'model') and self.device == "cuda":
                self.model.cpu()
                torch.cuda.empty_cache()
        except Exception as e:
            logging.error(f"清理资源时出错: {e}")