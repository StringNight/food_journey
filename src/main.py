from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
from .logging_config import configure_logging

# 配置日志
configure_logging()

from src.routers import auth, profile, chat
from src.database import Base, engine

logger = logging.getLogger(__name__)

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Food Journey API")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该指定具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建头像上传目录（这个是必需的，因为用于存储用户头像）
os.makedirs("uploads/avatars", exist_ok=True)

# 挂载头像静态文件
app.mount("/avatars", StaticFiles(directory="uploads/avatars"), name="avatars")

# 包含路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(profile.router, prefix="/api/profile", tags=["用户档案"])
app.include_router(chat.router, prefix="/api/chat", tags=["聊天"])

@app.get("/")
async def root():
    return {"message": "Welcome to Food Journey API"}