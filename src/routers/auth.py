"""用户认证相关的路由处理模块"""

import uuid
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
import logging
from collections import defaultdict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from passlib.context import CryptContext

from ..config import config
from ..models.user import User
from ..schemas.auth import (
    UserCreate, UserLogin, Token, UserResponse,
    RegisterResponse, LoginResponse, LoginJsonResponse,
    ChangePassword, ValidationErrorResponse, RateLimitErrorResponse, ErrorResponse, AccountLockedErrorResponse
)
from ..utils.auth import (
    get_password_hash, verify_password,
    create_access_token, get_current_user
)
from ..services.file import file_service
from ..database import get_db
from ..utils.cache import CacheManager, get_cache_manager
from ..utils.auth_utils import (
    is_account_locked, increment_failed_attempts,
    reset_failed_attempts, get_user_by_username
)
from ..config.limiter import limiter
from ..config.settings import settings

# 设置日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建路由处理器
router = APIRouter()

# 创建OAuth2密码Bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 锁定配置
MAX_LOGIN_ATTEMPTS = settings.MAX_LOGIN_ATTEMPTS  # 最大尝试次数
LOCKOUT_DURATION = int(os.getenv("LOCKOUT_DURATION", settings.LOCKOUT_DURATION))  # 从环境变量获取锁定时间，默认使用settings中的值
IS_TESTING = os.getenv("TESTING", "false").lower() == "true"  # 从环境变量获取测试标志

async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    """验证用户身份
    
    Args:
        db: 数据库会话
        username: 用户名
        password: 密码
        
    Returns:
        Optional[User]: 如果验证成功返回用户对象，否则返回None
    """
    try:
        user = await get_user_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    except Exception as e:
        logger.error(f"验证用户身份时发生错误: {str(e)}")
        return None

async def check_account_lockout(username: str, cache: CacheManager) -> None:
    """检查账户是否被锁定
    
    Args:
        username: 用户名
        cache: 缓存管理器
        
    Raises:
        HTTPException: 如果账户被锁定则抛出异常
    """
    is_locked, remaining_time = await is_account_locked(cache, username)
    if is_locked:
        if IS_TESTING:
            message = f"账户已被锁定，请在 {max(1, remaining_time)} 秒后重试"
        else:
            message = f"账户已被锁定，请在 {max(1, int(remaining_time / 60))} 分钟后重试"
            
        logger.warning(f"尝试访问被锁定的账户: username={username}, remaining_time={remaining_time}秒")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
            headers={
                "X-Error-Type": "account_locked",
                "X-Remaining-Time": str(remaining_time)
            }
        )

async def record_failed_login(username: str, cache: CacheManager) -> None:
    """记录登录失败尝试
    
    Args:
        username: 用户名
        cache: 缓存管理器
    """
    await increment_failed_attempts(cache, username)
    
    # 获取当前尝试次数
    key = f"login_attempts:{username}"
    attempts = await cache.get(key)
    logger.warning(f"登录失败: username={username}, attempts={attempts}/{MAX_LOGIN_ATTEMPTS}")

async def reset_failed_login_attempts(username: str, cache: CacheManager) -> None:
    """重置登录失败计数
    
    Args:
        username: 用户名
        cache: 缓存管理器
    """
    await reset_failed_attempts(cache, username)
    logger.info(f"重置登录失败计数: username={username}")

# 路由处理器
@router.post("/register", 
    response_model=RegisterResponse,
    responses={
        400: {"model": ValidationErrorResponse},
        429: {"model": RateLimitErrorResponse},
        500: {"model": ErrorResponse}
    }
)
@limiter.limit("60/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache_manager)
) -> JSONResponse:
    """
    用户注册接口
    
    Args:
        request: 请求对象
        user_data: 用户注册数据
        db: 数据库会话
        cache: 缓存管理器
        
    Returns:
        JSONResponse: 包含访问令牌和用户信息的响应
        
    Raises:
        HTTPException: 当注册过程中出现错误时抛出
    """
    try:
        # 记录开始注册
        logger.info(f"开始用户注册: username={user_data.username}")
        
        # 检查用户名是否已存在
        existing_user = await get_user_by_username(db, user_data.username)
        if existing_user:
            logger.warning(f"用户名已存在: username={user_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
            
        # 创建新用户
        user = User(
            id=str(uuid.uuid4()),
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # 生成访问令牌
        access_token, expires_in = create_access_token(data={"sub": user.id})
        
        # 记录注册成功
        logger.info(f"用户注册成功: user_id={user.id} username={user.username}")
        
        # 构造响应数据
        response_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "avatar_url": user.avatar_url,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "login_count": user.login_count
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data
        )
        
    except HTTPException as e:
        # 记录HTTP异常
        logger.warning(f"用户注册失败: {str(e.detail)}")
        raise
        
    except Exception as e:
        # 记录未知错误
        logger.error(f"用户注册过程中发生未知错误: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册过程中发生错误，请稍后重试"
        )

@router.post("/login",
    response_model=LoginResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": AccountLockedErrorResponse},
        429: {"model": RateLimitErrorResponse},
        500: {"model": ErrorResponse}
    }
)
@limiter.limit("60/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache_manager)
) -> JSONResponse:
    """用户登录
    
    Args:
        request: 请求对象
        form_data: 表单数据，包含用户名和密码
        db: 数据库会话
        cache: 缓存管理器
        
    Returns:
        JSONResponse: 包含访问令牌和用户信息的响应
    """
    try:
        # 记录开始处理登录请求
        logger.info(f"开始处理用户登录请求: username={form_data.username}")
        
        # 检查账户是否被锁定
        is_locked, remaining_time = await is_account_locked(cache, form_data.username)
        if is_locked:
            logger.warning(f"账户已被锁定: username={form_data.username}, remaining_time={remaining_time}秒")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"账户已被锁定，请在{remaining_time}秒后重试"
            )
        
        # 验证用户身份
        user = await authenticate_user(db, form_data.username, form_data.password)
        if not user:
            # 记录失败尝试
            attempts = await increment_failed_attempts(cache, form_data.username)
            logger.warning(f"登录失败，用户名或密码错误: username={form_data.username}, attempts={attempts}")
            
            # 如果达到最大尝试次数，返回锁定信息
            if attempts >= settings.MAX_LOGIN_ATTEMPTS:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"登录失败次数过多，账户已被锁定{settings.LOCKOUT_DURATION}分钟"
                )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"用户名或密码错误，还剩{settings.MAX_LOGIN_ATTEMPTS - attempts}次尝试机会"
            )
            
        # 重置失败尝试计数
        await reset_failed_attempts(cache, form_data.username)
        
        # 更新用户登录信息
        user.last_login = datetime.now()
        user.login_count += 1
        user.updated_at = datetime.now()
        await db.commit()
        
        # 生成访问令牌
        access_token, expires_in = create_access_token(data={"sub": str(user.id)})
        
        # 记录登录成功
        logger.info(f"用户登录成功: user_id={user.id} username={user.username}")
        
        # 构造响应数据
        response_data = {
            "token": {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": expires_in
            },
            "user": {
                "id": str(user.id),
                "username": user.username,
                "avatar_url": user.avatar_url,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "login_count": user.login_count
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录过程中发生未知错误: error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )

@router.post("/login/json",
    response_model=LoginJsonResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": AccountLockedErrorResponse},
        429: {"model": RateLimitErrorResponse},
        500: {"model": ErrorResponse}
    }
)
@limiter.limit("60/minute")
async def login_json(
    request: Request,
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
    cache: CacheManager = Depends(get_cache_manager)
) -> JSONResponse:
    """用户登录（JSON格式）
    
    Args:
        request: 请求对象
        user_data: 用户登录数据
        db: 数据库会话
        cache: 缓存管理器
        
    Returns:
        JSONResponse: 包含访问令牌和用户信息的响应
    """
    try:
        # 记录开始处理登录请求
        logger.info(f"开始处理用户JSON登录请求: username={user_data.username}")
        
        # 检查账户是否被锁定
        is_locked, remaining_time = await is_account_locked(cache, user_data.username)
        if is_locked:
            logger.warning(f"账户已被锁定: username={user_data.username}, remaining_time={remaining_time}秒")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"账户已被锁定，请在{remaining_time}秒后重试"
            )
        
        # 验证用户身份
        user = await authenticate_user(db, user_data.username, user_data.password)
        if not user:
            # 记录失败尝试
            attempts = await increment_failed_attempts(cache, user_data.username)
            logger.warning(f"登录失败，用户名或密码错误: username={user_data.username}, attempts={attempts}")
            
            # 如果达到最大尝试次数，返回锁定信息
            if attempts >= settings.MAX_LOGIN_ATTEMPTS:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"登录失败次数过多，账户已被锁定{settings.LOCKOUT_DURATION}分钟"
                )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"用户名或密码错误，还剩{settings.MAX_LOGIN_ATTEMPTS - attempts}次尝试机会"
            )
            
        # 重置失败尝试计数
        await reset_failed_attempts(cache, user_data.username)
        
        # 更新用户登录信息
        user.last_login = datetime.now()
        user.login_count += 1
        user.updated_at = datetime.now()
        await db.commit()
        
        # 生成访问令牌
        access_token, expires_in = create_access_token(data={"sub": str(user.id)})
        
        # 记录登录成功
        logger.info(f"用户登录成功: user_id={user.id}")
        
        # 构造响应数据
        response_data = {
            "token": {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": expires_in
            },
            "user": {
                "id": str(user.id),
                "username": user.username,
                "avatar_url": user.avatar_url,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "login_count": user.login_count
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录过程中发生未知错误: error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )

@router.get("/profile", response_model=UserResponse)
@limiter.limit("60/minute")
async def get_profile(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """获取用户个人资料
    
    返回当前登录用户的详细信息
    
    Args:
        request: 请求对象
        current_user: 当前登录用户
        
    Returns:
        JSONResponse: 用户详细信息
    """
    logger.info(f"开始获取用户资料: user_id={current_user.id}")
    
    try:
        response_data = {
            "id": str(current_user.id),
            "username": current_user.username,
            "avatar_url": current_user.avatar_url,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
            "login_count": current_user.login_count
        }
        logger.info(f"获取用户资料成功: user_id={current_user.id}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data
        )
        
    except Exception as e:
        logger.error(f"获取用户资料失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户资料失败，请稍后重试"
        )

@router.post("/change-password", status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
async def change_password(
    request: Request,
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """修改密码
    
    验证当前密码并更新为新密码
    
    Args:
        request: 请求对象
        password_data: 密码修改数据
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        dict: 包含成功消息的响应
    """
    logger.info(f"开始修改密码: user_id={current_user.id}")
    
    try:
        # 验证当前密码
        if not verify_password(password_data.current_password, current_user.hashed_password):
            logger.warning(f"修改密码失败：当前密码错误 user_id={current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前密码错误"
            )
            
        # 生成新密码哈希
        try:
            new_password_hash = get_password_hash(password_data.new_password)
        except Exception as e:
            logger.error(f"生成密码哈希失败: user_id={current_user.id}, error={str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="密码加密失败"
            )
            
        # 更新密码
        try:
            current_user.hashed_password = new_password_hash
            current_user.updated_at = datetime.now()
            await db.commit()
        except SQLAlchemyError as e:
            logger.error(f"更新密码失败: user_id={current_user.id}, error={str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新密码失败"
            )
            
        logger.info(f"修改密码成功: user_id={current_user.id}")
        return {"message": "密码修改成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改密码过程中发生未知错误: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改密码失败，请稍后重试"
        )

@router.post("/avatar",
    response_model=UserResponse,
    responses={
        400: {"model": ValidationErrorResponse},
        413: {"model": ValidationErrorResponse},
        401: {"model": ErrorResponse},
        429: {"model": RateLimitErrorResponse},
        500: {"model": ErrorResponse}
    }
)
@limiter.limit("60/minute")
async def avatar(
    request: Request,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """上传用户头像
    
    Args:
        file: 上传的头像文件
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        JSONResponse: 包含用户信息的响应
        
    Raises:
        HTTPException: 当文件大小超过限制或类型不支持时抛出
    """
    try:
        # 使用文件服务保存头像
        avatar_url = await file_service.save_avatar(file, str(current_user.id))
        
        # 更新用户头像URL
        current_user.avatar_url = avatar_url
        current_user.updated_at = datetime.now()
        
        try:
            await db.commit()
            logger.info(f"用户头像更新成功: user_id={current_user.id}")
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"更新用户头像失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新用户头像失败，请稍后重试"
            )
            
        # 返回更新后的用户信息
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(current_user.id),
                "username": current_user.username,
                "avatar_url": current_user.avatar_url,
                "is_active": current_user.is_active,
                "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
                "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
                "login_count": current_user.login_count
            }
        )
        
    except HTTPException as e:
        # 记录错误并重新抛出
        logger.warning(
            f"头像上传失败: user_id={current_user.id}, "
            f"status_code={e.status_code}, detail={e.detail}, "
            f"content_type={file.content_type}, size={file.size}"
        )
        raise
    except Exception as e:
        logger.error(f"头像上传过程中发生未知错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="头像上传失败，请稍后重试"
        )

@router.post("/refresh",
    response_model=LoginResponse,
    responses={
        401: {"model": ErrorResponse},
        429: {"model": RateLimitErrorResponse},
        500: {"model": ErrorResponse}
    }
)
@limiter.limit("60/minute")
async def refresh_token(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """刷新访问令牌
    
    为当前用户生成新的访问令牌，并返回用户信息
    
    Args:
        request: 请求对象
        current_user: 当前登录用户
        
    Returns:
        JSONResponse: 包含新访问令牌和用户信息的响应
    """
    logger.info(f"开始刷新令牌: user_id={current_user.id}")
    
    try:
        # 创建新的访问令牌
        access_token, expires_in = create_access_token(
            data={
                "sub": str(current_user.id),
                "refresh_time": datetime.now().timestamp()
            }
        )
        
        # 记录成功日志
        logger.info(f"令牌刷新成功: user_id={current_user.id}")
        
        # 构造响应数据
        response_data = {
            "token": {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": expires_in
            },
            "user": {
                "id": str(current_user.id),
                "username": current_user.username,
                "avatar_url": current_user.avatar_url,
                "is_active": current_user.is_active,
                "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
                "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
                "login_count": current_user.login_count
            }
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data
        )
        
    except Exception as e:
        logger.error(f"刷新令牌过程中发生错误: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刷新令牌失败，请稍后重试"
        )

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("60/minute")
async def delete_user(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """删除当前用户账户
    
    删除用户账户及其所有相关数据，包括：
    - 用户基本信息
    - 用户配置文件
    - 用户创建的菜谱
    - 用户的收藏
    - 用户的评分记录
    - 用户的运动记录
    - 用户的营养记录
    
    Args:
        request: 请求对象
        current_user: 当前登录用户
        db: 数据库会话
        
    Returns:
        None: 返回204状态码
    """
    logger.info(f"开始删除用户账户: user_id={current_user.id}")
    
    try:
        # 删除用户数据
        try:
            # 删除用户头像文件
            if current_user.avatar_url:
                try:
                    await file_service.delete_file(current_user.avatar_url)
                except Exception as e:
                    logger.warning(f"删除用户头像文件失败: user_id={current_user.id}, error={str(e)}")
            
            # 删除用户记录
            await db.delete(current_user)
            await db.commit()
            
        except SQLAlchemyError as e:
            logger.error(f"删除用户数据失败: user_id={current_user.id}, error={str(e)}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除用户数据失败"
            )
        
        # 记录成功日志
        logger.info(f"用户账户删除成功: user_id={current_user.id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户账户过程中发生未知错误: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户账户失败，请稍后重试"
        )