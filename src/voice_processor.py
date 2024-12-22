import logging
import torch
import torchaudio
import numpy as np
from wenet.transformer.asr_model import init_asr_model
from wenet.utils.common import get_args
from wenet.utils.file_utils import read_symbol_table

class VoiceProcessor:
    def __init__(self):
        try:
            # 强制使用 CPU 设备
            self.device = "cpu"
            logging.info(f"使用 {self.device} 设备进行语音处理")
            
            # 加载 WeNet 配置
            args = get_args()
            args.config = "configs/wenetspeech_conformer.yaml"  # WeNet 配置文件路径
            args.dict = "data/dict/lang_char.txt"  # 字典文件路径
            args.checkpoint = "exp/conformer/final.pt"  # 模型文件路径
            
            # 加载字典
            self.symbol_table = read_symbol_table(args.dict)
            
            # 加载模型
            self.model = init_asr_model(args)
            self.model.load_state_dict(torch.load(args.checkpoint, map_location=self.device))
            self.model.eval()
            
            logging.info("语音处理器初始化成功")
            
        except Exception as e:
            logging.error(f"语音处理器初始化失败: {e}")
            raise
    
    def process_voice(self, audio_file) -> str:
        try:
            # 加载音频文件
            waveform, sample_rate = torchaudio.load(audio_file)
            
            # 重采样到 16kHz（如果需要）
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                waveform = resampler(waveform)
                sample_rate = 16000
            
            # 确保音频是单声道
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # 特征提取和归一化
            feature = torchaudio.compliance.kaldi.fbank(
                waveform,
                num_mel_bins=80,
                frame_length=25,
                frame_shift=10,
                dither=0.0
            )
            feature = feature.unsqueeze(0)  # 添加批次维度
            
            # 进行语音识别
            with torch.no_grad():
                hyps = self.model.recognize(
                    feature,
                    beam_size=5,
                    decoding_chunk_size=-1,
                    num_decoding_left_chunks=-1,
                    simulate_streaming=False
                )
            
            # 解码结果
            result = "".join([self.symbol_table[i] for i in hyps[0][0]])
            return result
            
        except Exception as e:
            logging.error(f"语音处理失败: {e}")
            return "无法识别语音内容" 