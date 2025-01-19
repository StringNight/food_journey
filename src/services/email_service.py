from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv
import logging
from jose import jwt
from datetime import datetime, timedelta, UTC

# 加载环境变量
load_dotenv()

# 邮件配置
mail_config = {
    "MAIL_USERNAME": os.getenv("MAIL_USERNAME", "test@example.com"),
    "MAIL_PASSWORD": os.getenv("MAIL_PASSWORD", "password"),
    "MAIL_FROM": os.getenv("MAIL_FROM", "test@example.com"),
    "MAIL_PORT": int(os.getenv("MAIL_PORT", "587")),
    "MAIL_SERVER": os.getenv("MAIL_SERVER", "smtp.example.com"),
    "MAIL_STARTTLS": True,
    "MAIL_SSL_TLS": False,
    "USE_CREDENTIALS": True
}

class EmailService:
    """邮件服务类"""
    
    def __init__(self):
        """初始化邮件服务"""
        try:
            self.conf = ConnectionConfig(**mail_config)
            self.fastmail = FastMail(self.conf)
            self.is_available = True
        except Exception as e:
            logging.warning(f"邮件服务初始化失败: {e}")
            self.is_available = False
        self.reset_token_secret = os.getenv("RESET_TOKEN_SECRET", "your-reset-token-secret")
    
    def create_reset_token(self, email: str) -> str:
        """创建重置密码令牌"""
        expire = datetime.now(UTC) + timedelta(hours=24)
        return jwt.encode(
            {"email": email, "exp": expire},
            self.reset_token_secret,
            algorithm="HS256"
        )
    
    def verify_reset_token(self, token: str) -> str:
        """验证重置密码令牌"""
        try:
            payload = jwt.decode(
                token,
                self.reset_token_secret,
                algorithms=["HS256"]
            )
            return payload["email"]
        except jwt.InvalidTokenError:
            raise ValueError("无效的重置密码令牌")
    
    async def send_reset_password_email(self, email: EmailStr, reset_token: str):
        """发送重置密码邮件"""
        if not self.is_available:
            logging.warning("邮件服务未正确配置，无法发送邮件")
            return
            
        # 构建重置密码链接
        reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
        
        # 邮件内容
        html = f"""
        <p>您好！</p>
        <p>我们收到了重置您密码的请求。如果这不是您本人的操作，请忽略此邮件。</p>
        <p>点击下面的链接重置密码（链接24小时内有效）：</p>
        <p><a href="{reset_url}">{reset_url}</a></p>
        <p>如果您无法点击链接，请复制链接到浏览器地址栏访问。</p>
        <p>祝您使用愉快！</p>
        <p>美食之旅团队</p>
        """
        
        try:
            message = MessageSchema(
                subject="重置密码 - 美食之旅",
                recipients=[email],
                body=html,
                subtype="html"
            )
            await self.fastmail.send_message(message)
            logging.info(f"重置密码邮件发送成功: {email}")
        except Exception as e:
            logging.error(f"发送重置密码邮件失败: {e}")
            raise 