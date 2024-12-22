from ultralytics import YOLO
import cv2
import logging
from typing import Dict, List
import numpy as np
import base64
import json
from alibabacloud_imagerecog20190930.client import Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_imagerecog20190930 import models as imagerecog_models
from alibabacloud_tea_util import models as util_models
import os
import oss2
import uuid

class ImageProcessor:
    def __init__(self):
        """初始化图像处理器"""
        try:
            # 从环境变量获取阿里云配置
            self.access_key_id = os.getenv('ALIYUN_ACCESS_KEY_ID')
            self.access_key_secret = os.getenv('ALIYUN_ACCESS_KEY_SECRET')
            self.endpoint = os.getenv('ALIYUN_OSS_ENDPOINT')
            self.bucket_name = os.getenv('ALIYUN_OSS_BUCKET_NAME')
            
            if not all([self.access_key_id, self.access_key_secret, self.endpoint, self.bucket_name]):
                raise ValueError("缺少必要的阿里云配置")

            # 初始化阿里云图像识别客户端
            config = open_api_models.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret
            )
            config.endpoint = 'imagerecog.cn-shanghai.aliyuncs.com'
            self.client = Client(config)

            # 初始化 OSS 客户端
            auth = oss2.Auth(self.access_key_id, self.access_key_secret)
            self.bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)

            logging.info("图像处理器初始化成功")

        except Exception as e:
            logging.error(f"图像处理器初始化失败: {str(e)}")
            raise

    def upload_to_oss(self, image_data):
        """上传图片到OSS并返回URL"""
        object_name = f"food_images/{uuid.uuid4()}.jpg"
        self.bucket.put_object(object_name, image_data)
        return f"https://{self.bucket_name}.{self.endpoint}/{object_name}"

    def process_image(self, image_file) -> str:
        """处理图像并返回检测到的食物描述"""
        try:
            # 读取图片文件
            if isinstance(image_file, str):  # 如果是文件路径
                with open(image_file, 'rb') as f:
                    img_data = f.read()
            elif isinstance(image_file, dict) and 'path' in image_file:  # Gradio上传的文件
                with open(image_file['path'], 'rb') as f:
                    img_data = f.read()
            else:
                return "不支持的图片格式"

            # 上传图片到OSS并获取URL
            image_url = self.upload_to_oss(img_data)
            print(f"图片已上传到OSS，URL: {image_url}")

            # 创建识别请求
            recognize_request = imagerecog_models.RecognizeFoodRequest(
                image_url=image_url
            )
            runtime = util_models.RuntimeOptions()
            
            print("发送识别请求...")  # 调试信息
            
            # 发送请求并获取响应
            response = self.client.recognize_food_with_options(recognize_request, runtime)
            
            print("收到响应...")  # 调试信息
            
            if not response.body.data or not response.body.data.top_5_list:
                return "未能在图片中检测到食物。"

            # 处理识别结果
            results = []
            for item in response.body.data.top_5_list:
                score_percentage = round(float(item.score) * 100, 2)
                results.append(f"{item.score_name}（置信度：{score_percentage}%）")

            # 生成描述文本
            description = "图片中检测到以下食物：\n" + "\n".join(results)
            
            # 在终端打印识别结果
            print(f"识别结果: {description}")

            # 添加卡路里信息（如果有）
            if hasattr(response.body.data, 'calorie') and response.body.data.calorie:
                description += f"\n\n预估卡路里：{response.body.data.calorie} 千卡/100克"
                
            return description

        except Exception as e:
            print(f"图片处理失败: {e}")
            print(f"错误详情: {str(e)}")  # 添加更详细的错误信息
            return f"图片处理失败：{str(e)}"

    def visualize_results(self, image_file: str, results) -> str:
        """可视化检测结果"""
        try:
            image = cv2.imread(image_file)
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # 获取边界框坐标
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    name = self.model.names[cls_id]
                    size = self.estimate_relative_size([x1, y1, x2, y2])
                    
                    # 绘制边界框
                    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # 添加标签
                    label = f"{name} ({size}) {conf:.2f}"
                    cv2.putText(image, label, (x1, y1-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # 保存结果
            output_path = image_file.replace('.', '_detected.')
            cv2.imwrite(output_path, image)
            return output_path
            
        except Exception as e:
            logging.error(f"可视化结果失败: {e}")
            return None