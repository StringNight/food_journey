import os
import requests
import logging
from tqdm import tqdm

def download_file(url, filename):
    """下载文件并显示进度条"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as f, tqdm(
        desc=filename,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for data in response.iter_content(chunk_size=1024):
            size = f.write(data)
            pbar.update(size)

def main():
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建必要的目录
    os.makedirs("exp/conformer", exist_ok=True)
    
    # 模型文件 URL（这里使用 WeNet 提供的中文预训练模型）
    model_url = "https://wenet-1256283475.cos.ap-shanghai.myqcloud.com/models/wenetspeech/wenetspeech_u2pp_conformer_exp.tar.gz"
    
    try:
        logging.info("开始下载预训练模型...")
        download_file(model_url, "exp/conformer/model.tar.gz")
        
        logging.info("解压模型文件...")
        os.system("cd exp/conformer && tar xzf model.tar.gz")
        
        logging.info("清理临时文件...")
        os.remove("exp/conformer/model.tar.gz")
        
        # 重命名模型文件
        os.rename(
            "exp/conformer/20220506_u2pp_conformer_exp/final.pt",
            "exp/conformer/final.pt"
        )
        
        logging.info("模型下载和配置完成！")
        
    except Exception as e:
        logging.error(f"下载或配置模型时出错: {e}")
        raise

if __name__ == "__main__":
    main() 