from datetime import datetime
from pathlib import Path
from typing import Optional, Set
import logging
from fastapi import UploadFile, HTTPException, status
import aiofiles
import magic
import re

# 配置日志
logger = logging.getLogger(__name__)

class FileService:
    """文件服务
    
    处理文件上传、验证和存储等操作
    """
    
    # 允许的文件类型
    ALLOWED_IMAGE_TYPES: Set[str] = {
        'image/jpeg',
        'image/png',
        'image/gif'
    }
    
    ALLOWED_AUDIO_TYPES: Set[str] = {
        'audio/wav',
        'audio/mpeg',
        'audio/mp3',
        'audio/m4a'
    }
    
    # 文件大小限制
    MAX_IMAGE_SIZE: int = 5 * 1024 * 1024  # 5MB
    MAX_AUDIO_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, base_upload_dir: str = "uploads"):
        self.base_upload_dir = Path(base_upload_dir)
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)
        
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名
        
        移除不安全的字符，只保留字母、数字、下划线、连字符和点
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 清理后的文件名
        """
        # 获取文件扩展名
        name, ext = Path(filename).stem, Path(filename).suffix
        
        # 清理文件名
        name = re.sub(r'[^\w\-\.]', '_', name)
        
        # 限制文件名长度
        if len(name) > 32:
            name = name[:32]
            
        return f"{name}{ext}"
        
    async def _verify_file_type(
        self,
        file: UploadFile,
        allowed_types: Set[str],
        error_message: str
    ) -> bytes:
        """验证文件类型
        
        Args:
            file: 上传的文件
            allowed_types: 允许的MIME类型集合
            error_message: 类型错误时的提示消息
            
        Returns:
            bytes: 文件内容
            
        Raises:
            HTTPException: 文件类型不允许时抛出
        """
        content = await file.read()
        
        try:
            # 使用python-magic检测实际的MIME类型
            mime_type = magic.from_buffer(content, mime=True)
            logger.debug(f"检测到的MIME类型: {mime_type}")
            
            if mime_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{error_message} (检测到的类型: {mime_type})",
                    headers={"X-Error-Type": "invalid_file_type"}
                )
                
            return content
            
        except magic.MagicException as e:
            logger.error(f"文件类型检测失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件类型检测失败: {str(e)}",
                headers={"X-Error-Type": "magic_detection_failed"}
            )
            
    async def save_file(
        self,
        file: UploadFile,
        subdir: str,
        allowed_types: Set[str],
        max_size: int,
        error_message: str,
        user_id: Optional[str] = None
    ) -> str:
        """保存文件
        
        Args:
            file: 上传的文件
            subdir: 子目录名
            allowed_types: 允许的MIME类型集合
            max_size: 最大文件大小(字节)
            error_message: 类型错误时的提示消息
            user_id: 用户ID(可选)
            
        Returns:
            str: 文件的相对URL路径
            
        Raises:
            HTTPException: 文件验证失败时抛出
        """
        try:
            # 首先验证文件大小
            if file.size > max_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"文件大小超过限制: {max_size/1024/1024:.1f}MB"
                )
            
            # 验证并获取文件内容
            content = await self._verify_file_type(file, allowed_types, error_message)
            
            # 准备保存目录
            save_dir = self.base_upload_dir / subdir
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self._sanitize_filename(file.filename)
            if user_id:
                save_path = save_dir / f"{user_id}_{timestamp}_{filename}"
            else:
                save_path = save_dir / f"{timestamp}_{filename}"
            
            # 保存文件
            async with aiofiles.open(save_path, 'wb') as f:
                await f.write(content)
            
            # 返回相对URL
            return f"/{subdir}/{save_path.name}"
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"保存文件失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="保存文件失败"
            )
            
    async def save_avatar(self, file: UploadFile, user_id: str) -> str:
        """保存头像
        
        Args:
            file: 上传的头像文件
            user_id: 用户ID
            
        Returns:
            str: 头像的相对URL路径
        """
        return await self.save_file(
            file=file,
            subdir="avatars",
            allowed_types=self.ALLOWED_IMAGE_TYPES,
            max_size=self.MAX_IMAGE_SIZE,
            error_message="不支持的图片格式",
            user_id=user_id
        )
        
    async def save_voice(self, file: UploadFile, user_id: Optional[str] = None) -> str:
        """保存语音文件
        
        Args:
            file: 上传的语音文件
            user_id: 用户ID(可选)
            
        Returns:
            str: 语音文件的相对URL路径
        """
        return await self.save_file(
            file=file,
            subdir="voices",
            allowed_types=self.ALLOWED_AUDIO_TYPES,
            max_size=self.MAX_AUDIO_SIZE,
            error_message="不支持的音频格式",
            user_id=user_id
        )
        
    async def save_image(self, file: UploadFile, user_id: Optional[str] = None) -> str:
        """保存图片
        
        Args:
            file: 上传的图片文件
            user_id: 用户ID(可选)
            
        Returns:
            str: 图片的相对URL路径
        """
        return await self.save_file(
            file=file,
            subdir="images",
            allowed_types=self.ALLOWED_IMAGE_TYPES,
            max_size=self.MAX_IMAGE_SIZE,
            error_message="不支持的图片格式",
            user_id=user_id
        )

# 创建服务实例
file_service = FileService() 