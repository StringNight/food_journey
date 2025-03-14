from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import os
import logging
from .config import config, setup_cors
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import traceback
from .middleware.version import VersionMiddleware
from .docs import custom_openapi
import asyncio
from .config.limiter import limiter

# 配置日志级别为INFO或DEBUG以查看更多日志
logging.getLogger().setLevel(logging.INFO)  # 或者使用logging.DEBUG查看所有日志
logging.getLogger('uvicorn').setLevel(logging.INFO)
logging.getLogger('fastapi').setLevel(logging.INFO)
logging.getLogger('httpx').setLevel(logging.WARNING)  # 这些库的日志可能太多，保持WARNING级别
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)
logging.getLogger('gradio').setLevel(logging.INFO)

# 导入所有模型以确保在创建表之前加载它们
from .models import (
    User, UserProfileModel, RecipeModel, RatingModel,
    FavoriteModel, ChatMessageModel, ExerciseRecord,
    ExerciseSet, MealRecord, DailyNutritionSummary
)
from .database import Base, engine
from .routers import auth, profile, chat, workout, recipes, favorites

logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="Food Journey API",
    description="Food Journey 应用的后端 API",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI 路由
    redoc_url="/redoc",  # ReDoc 路由
    openapi_url="/openapi.json"  # OpenAPI JSON 路由
)

# 配置速率限制中间件
app.state.limiter = limiter

# 添加速率限制异常处理
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": str(exc)}
    )

# 添加响应包装中间件
@app.middleware("http")
async def response_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        
        # 如果响应已经是 JSONResponse 或 Response 类型，直接返回
        if isinstance(response, (JSONResponse, Response)):
            return response
            
        # 如果响应是字典，转换为 JSONResponse
        if isinstance(response, dict):
            return JSONResponse(
                content=response,
                status_code=200
            )
            
        # 如果响应是其他类型，尝试转换为字符串并包装在 JSONResponse 中
        return JSONResponse(
            content={"data": str(response)},
            status_code=200
        )
    except Exception as e:
        logger.error(f"响应处理失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误"}
        )

# 创建数据库表
async def init_db():
    """初始化数据库表结构"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表初始化成功")
    except Exception as e:
        logger.error(f"数据库表初始化失败: {str(e)}")
        raise

# 在应用启动时初始化
@app.on_event("startup")
async def startup_event():
    """应用启动时的事件处理"""
    await init_db()
    logger.info("应用启动初始化完成")

# 配置 CORS
setup_cors(app)

# 添加版本控制中间件
app.add_middleware(VersionMiddleware)

# 创建头像上传目录
os.makedirs(config.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(config.UPLOAD_DIR, "avatars"), exist_ok=True)

# 挂载头像静态文件
app.mount("/avatars", StaticFiles(directory=os.path.join(config.UPLOAD_DIR, "avatars")), name="avatars")

# 添加路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(profile.router, prefix="/api/v1/profile", tags=["用户档案"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["聊天"])
app.include_router(recipes.router, prefix="/api/v1/recipes", tags=["食谱"])
app.include_router(favorites.router, prefix="/api/v1/favorites", tags=["收藏"])
app.include_router(workout.router, prefix="/api/v1/workouts", tags=["运动"])

app.openapi = lambda: custom_openapi(app)  # 绑定自定义OpenAPI生成函数，确保文档端点可访问

@app.get("/")
@limiter.limit("10/minute")  # 每分钟最多10个请求
async def root(request: Request):
    """根路径处理器"""
    return {"message": "Welcome to Food Journey API"}

# 全局错误处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """处理HTTP异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "type": "http_error"
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """处理值错误"""
    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc),
            "type": "value_error"
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    # 提取所有错误信息
    error_details = []
    for error in exc.errors():
        # 提取字段位置
        field = error["loc"][-1] if error["loc"] else "unknown_field"
        field_path = ".".join(str(loc) for loc in error["loc"])
        
        # 获取错误消息和类型
        error_msg = error["msg"]
        error_type = error["type"]
        
        error_details.append({
            "field": field,
            "field_path": field_path,
            "message": error_msg,
            "type": error_type
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "输入数据验证失败",
            "type": "validation_error",
            "errors": error_details
        }
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """处理数据库错误"""
    logger.error(f"数据库错误: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "数据库操作失败",
            "type": "database_error"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理其他未捕获的异常"""
    logger.error(f"未捕获的异常: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误",
            "type": "internal_error"
        }
    )

# 如果是直接运行此文件（不是作为模块导入）
if __name__ == "__main__":
    import uvicorn
    import os
    from pathlib import Path
    
    # 获取SSL配置
    use_https = os.getenv("USE_HTTPS", "false").lower() == "true"
    ssl_certfile = os.getenv("SSL_CERTFILE")
    ssl_keyfile = os.getenv("SSL_KEYFILE")
    
    # 展开路径中的用户目录符号 (~)
    if ssl_certfile:
        ssl_certfile = os.path.expanduser(ssl_certfile)
    if ssl_keyfile:
        ssl_keyfile = os.path.expanduser(ssl_keyfile)
    
    # 配置SSL
    ssl_config = {}
    if use_https and ssl_certfile and ssl_keyfile:
        if os.path.exists(ssl_certfile) and os.path.exists(ssl_keyfile):
            ssl_config.update({
                "ssl_keyfile": ssl_keyfile,
                "ssl_certfile": ssl_certfile
            })
        else:
            print("警告: SSL证书文件不存在，将使用HTTP模式启动")
    
    # 启动服务器
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        **ssl_config
    )