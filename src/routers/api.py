from fastapi import APIRouter
from . import auth, profile, chat, recipes, favorites

router = APIRouter()

# 包含各个子路由
router.include_router(auth.router, prefix="/auth", tags=["认证"])
router.include_router(profile.router, prefix="/profile", tags=["用户档案"])
router.include_router(chat.router, prefix="/chat", tags=["聊天"])
router.include_router(recipes.router, prefix="/recipes", tags=["食谱"])
router.include_router(favorites.router, prefix="/favorites", tags=["收藏"]) 