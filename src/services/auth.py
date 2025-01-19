from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import uuid
from typing import Tuple, Dict, Optional
import logging
from fastapi import HTTPException, status

from ..config.settings import settings
from ..models.user import User

# 配置日志
logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """认证服务
    
    处理密码加密、验证和令牌生成等认证相关操作
    """
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        
        # 令牌黑名单，用于存储已撤销的令牌
        self.token_blacklist: Dict[str, datetime] = {}
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希后的密码
            
        Returns:
            bool: 密码是否匹配
        """
        return pwd_context.verify(plain_password, hashed_password)
        
    def get_password_hash(self, password: str) -> str:
        """生成密码哈希
        
        Args:
            password: 明文密码
            
        Returns:
            str: 哈希后的密码
        """
        return pwd_context.hash(password)
        
    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> Tuple[str, int]:
        """创建访问令牌
        
        Args:
            data: 要编码到令牌中的数据
            expires_delta: 过期时间增量，如果未指定则使用默认值
            
        Returns:
            Tuple[str, int]: 令牌字符串和过期时间（秒）
        """
        to_encode = data.copy()
        
        # 设置过期时间
        if expires_delta:
            expire = datetime.now() + expires_delta
        else:
            expire = datetime.now() + timedelta(
                minutes=self.access_token_expire_minutes
            )
            
        # 添加标准声明
        to_encode.update({
            "exp": int(expire.timestamp()),
            "iat": int(datetime.now().timestamp()),
            "jti": str(uuid.uuid4())
        })
        
        # 创建令牌
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        return encoded_jwt, int(expire.timestamp() - datetime.now().timestamp())
        
    def verify_token(self, token: str) -> dict:
        """验证令牌
        
        Args:
            token: JWT令牌字符串
            
        Returns:
            dict: 解码后的令牌数据
            
        Raises:
            HTTPException: 令牌无效或已过期时抛出
        """
        try:
            # 解码令牌
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # 检查令牌是否在黑名单中
            jti = payload.get("jti")
            if jti in self.token_blacklist:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="令牌已被撤销",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return payload
            
        except JWTError as e:
            logger.error(f"令牌验证失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    def revoke_token(self, token: str) -> None:
        """撤销令牌
        
        将令牌添加到黑名单中
        
        Args:
            token: JWT令牌字符串
        """
        try:
            # 解码令牌以获取过期时间
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # 获取令牌唯一标识和过期时间
            jti = payload.get("jti")
            exp = datetime.fromtimestamp(payload.get("exp"))
            
            # 添加到黑名单
            self.token_blacklist[jti] = exp
            
            # 清理过期的黑名单条目
            self._cleanup_blacklist()
            
        except JWTError:
            pass  # 如果令牌已经无效，则忽略
            
    def _cleanup_blacklist(self) -> None:
        """清理过期的黑名单条目"""
        current_time = datetime.now()
        expired_jtis = [
            jti for jti, exp in self.token_blacklist.items()
            if exp <= current_time
        ]
        for jti in expired_jtis:
            self.token_blacklist.pop(jti)

# 创建服务实例
auth_service = AuthService() 