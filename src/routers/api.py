from fastapi import APIRouter
from src.routers import auth, profile, chat

router = APIRouter()

# 包含各个子路由
router.include_router(auth.router, prefix="/auth", tags=["认证"])
router.include_router(profile.router, prefix="/profile", tags=["用户档案"])
router.include_router(chat.router, prefix="/chat", tags=["聊天"]) 