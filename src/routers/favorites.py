from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from typing import List
from datetime import datetime
import uuid
from fastapi.responses import JSONResponse

from ..database import get_db
from ..models.user import User
from ..models.recipe import RecipeModel
from ..models.favorite import FavoriteModel
from ..schemas.favorite import FavoriteResponse, FavoriteListResponse, PaginationInfo, FavoriteRecipe, BatchFavoriteRequest
from ..schemas.recipe import Recipe
from ..auth.jwt import get_current_user
import logging

router = APIRouter(
    prefix="",
    tags=["favorites"]
)

@router.post("/batch-add", status_code=status.HTTP_201_CREATED)
async def batch_favorite_operations(
    request: BatchFavoriteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """批量添加收藏
    
    Args:
        request (BatchFavoriteRequest): 包含要收藏的食谱ID列表,最多10个
        current_user (User): 当前登录用户
        db (AsyncSession): 数据库会话
        
    Returns:
        dict: 包含以下字段:
            - schema_version (str): API版本号
            - message (str): 操作结果消息
            - favorites (List[dict]): 新增收藏列表,每个收藏包含recipe_id和created_at
            
    Raises:
        HTTPException: 
            - 400: 超过收藏数量限制(>10)或食谱不存在
            - 500: 服务器内部错误
    """
    try:
        recipe_ids = request.recipe_ids
        
        # 检查数量限制
        if len(recipe_ids) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="每次最多只能收藏10个食谱"
            )
            
        # 检查食谱是否存在
        recipes = await db.execute(
            select(RecipeModel).filter(RecipeModel.id.in_(recipe_ids))
        )
        existing_recipes = {recipe.id: recipe for recipe in recipes.scalars().all()}
        
        # 检查是否有不存在的食谱
        non_existent = [rid for rid in recipe_ids if rid not in existing_recipes]
        if non_existent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"以下食谱不存在: {', '.join(non_existent)}"
            )
            
        # 检查是否已经收藏
        existing_favorites = await db.execute(
            select(FavoriteModel).filter(
                FavoriteModel.user_id == current_user.id,
                FavoriteModel.recipe_id.in_(recipe_ids)
            )
        )
        existing_favorite_ids = {f.recipe_id for f in existing_favorites.scalars().all()}
        
        # 过滤掉已经收藏的食谱
        to_add = [rid for rid in recipe_ids if rid not in existing_favorite_ids]
        
        # 创建新的收藏记录
        created_at = datetime.now()
        new_favorites = []
        for recipe_id in to_add:
            favorite = FavoriteModel(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                recipe_id=recipe_id,
                created_at=created_at
            )
            db.add(favorite)
            new_favorites.append({
                "recipe_id": recipe_id,
                "created_at": created_at
            })
            
        await db.commit()
        
        return {
            "schema_version": "1.0",
            "message": "批量收藏成功",
            "favorites": new_favorites
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"批量添加收藏失败: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="批量添加收藏失败")

@router.post("/{recipe_id}", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """添加单个食谱到收藏
    
    Args:
        recipe_id (str): 要收藏的食谱ID
        current_user (User): 当前登录用户
        db (AsyncSession): 数据库会话
        
    Returns:
        FavoriteResponse: 收藏操作响应,包含:
            - schema_version: API版本号
            - message: 操作结果消息
            - recipe_id: 收藏的食谱ID
            - created_at: 收藏时间
            
    Raises:
        HTTPException:
            - 404: 食谱不存在
            - 400: 已经收藏过该食谱
            - 500: 服务器内部错误
    """
    try:
        # 检查食谱是否存在
        recipe = await db.execute(select(RecipeModel).filter(RecipeModel.id == recipe_id))
        recipe = recipe.scalar_one_or_none()
        if not recipe:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="食谱不存在")
            
        # 检查是否已经收藏
        existing_favorite = await db.execute(
            select(FavoriteModel).filter(
                FavoriteModel.user_id == current_user.id,
                FavoriteModel.recipe_id == recipe_id
            )
        )
        existing_favorite = existing_favorite.scalar_one_or_none()
        
        if existing_favorite:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已经收藏过该食谱")
            
        # 创建收藏记录
        created_at = datetime.now()
        favorite = FavoriteModel(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            recipe_id=recipe_id,
            created_at=created_at
        )
        db.add(favorite)
        await db.commit()
        
        return FavoriteResponse(
            schema_version="1.0",
            message="收藏成功",
            recipe_id=recipe_id,
            created_at=created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"添加收藏失败: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="添加收藏失败")

@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """取消收藏
    
    Args:
        recipe_id (str): 要取消收藏的食谱ID
        current_user (User): 当前登录用户
        db (AsyncSession): 数据库会话
        
    Returns:
        None: 成功返回204状态码
        
    Raises:
        HTTPException:
            - 404: 食谱不存在或收藏不存在
            - 403: 尝试删除其他用户的收藏
            - 500: 服务器内部错误
    """
    try:
        # 先检查记录是否存在
        existing_favorite = await db.execute(
            select(FavoriteModel).filter(
                FavoriteModel.recipe_id == recipe_id,
                FavoriteModel.user_id == current_user.id
            )
        )
        existing_favorite = existing_favorite.scalar_one_or_none()
        
        if not existing_favorite:
            # 检查是否是因为食谱不存在
            recipe = await db.execute(select(RecipeModel).filter(RecipeModel.id == recipe_id))
            recipe = recipe.scalar_one_or_none()
            if not recipe:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="食谱不存在")
            
            # 检查是否是其他用户的收藏
            other_favorite = await db.execute(
                select(FavoriteModel).filter(
                    FavoriteModel.recipe_id == recipe_id
                )
            )
            other_favorite = other_favorite.scalar_one_or_none()
            if other_favorite:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="FORBIDDEN"
                )
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="收藏不存在")
            
        # 删除收藏记录
        await db.execute(
            delete(FavoriteModel).filter(
                FavoriteModel.recipe_id == recipe_id,
                FavoriteModel.user_id == current_user.id
            )
        )
        await db.commit()
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"取消收藏失败: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="取消收藏失败")

@router.get("/", response_model=FavoriteListResponse)
async def list_favorites(
    page: int = 1,
    per_page: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的收藏列表
    
    Args:
        page (int, optional): 页码,默认为1
        per_page (int, optional): 每页数量,默认为20
        current_user (User): 当前登录用户
        db (AsyncSession): 数据库会话
        
    Returns:
        FavoriteListResponse: 收藏列表响应,包含:
            - schema_version: API版本号
            - favorites: 收藏的食谱列表
            - pagination: 分页信息(total, page, per_page, total_pages)
            
    Raises:
        HTTPException:
            - 500: 服务器内部错误
    """
    try:
        # 构建查询
        base_query = select(RecipeModel, FavoriteModel).join(
            FavoriteModel,
            FavoriteModel.recipe_id == RecipeModel.id
        ).filter(FavoriteModel.user_id == current_user.id)
        
        # 获取总数
        total_query = select(func.count()).select_from(FavoriteModel).filter(FavoriteModel.user_id == current_user.id)
        total = await db.scalar(total_query)
        
        total_pages = (total + per_page - 1) // per_page
        
        # 获取分页数据
        results = await db.execute(
            base_query.order_by(FavoriteModel.created_at.desc())\
                .offset((page - 1) * per_page)\
                .limit(per_page)
        )
        
        favorites = []
        for recipe, favorite in results.fetchall():
            favorite_recipe = FavoriteRecipe(
                id=recipe.id,
                title=recipe.title,
                description=recipe.description,
                ingredients=recipe.ingredients,
                steps=recipe.steps,
                cooking_time=recipe.cooking_time,
                difficulty=recipe.difficulty,
                cuisine_type=recipe.cuisine_type,
                author_id=recipe.author_id,
                created_at=favorite.created_at,
                views_count=recipe.views_count,
                average_rating=recipe.average_rating
            )
            favorites.append(favorite_recipe)
        
        return FavoriteListResponse(
            schema_version="1.0",
            favorites=favorites,
            pagination=PaginationInfo(
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages
            )
        )
        
    except Exception as e:
        logging.error(f"获取收藏列表失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取收藏列表失败") 