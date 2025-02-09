from fastapi import APIRouter
from . import auth, profile, chat, recipes, favorites

router = APIRouter()

# 包含各个子路由
router.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
router.include_router(profile.router, prefix="/api/v1/profile", tags=["用户档案"])
router.include_router(chat.router, prefix="/api/v1/chat", tags=["聊天"])
router.include_router(recipes.router, prefix="/api/v1/recipes", tags=["食谱"])
router.include_router(favorites.router, prefix="/api/v1/favorites", tags=["收藏"]) 