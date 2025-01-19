from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import logging
import uuid
from datetime import datetime, UTC
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from ..database import get_db
from ..models.recipe import RecipeModel as Recipe
from ..models.user import User
from ..models.rating import RatingModel as Rating
from ..schemas.recipe import RecipeCreate, RecipeResponse, RecipeUpdate, RecipeListResponse, RatingCreate, PaginationInfo
from ..auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe: RecipeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新菜谱
    
    参数:
        recipe (RecipeCreate): 菜谱创建模型，包含标题、描述、食材等信息
        current_user (User): 当前登录用户
        db (AsyncSession): 数据库会话
        
    返回:
        RecipeResponse: 创建成功的菜谱信息
        
    错误:
        422: 请求数据验证失败
        500: 服务器内部错误
    """
    try:
        # 数据验证
        if not recipe.title or not recipe.title.strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="菜谱标题不能为空")
        if not recipe.description or not recipe.description.strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="菜谱描述不能为空")
        if not recipe.ingredients or len(recipe.ingredients) == 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="食材列表不能为空")
        if not recipe.steps or len(recipe.steps) == 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="烹饪步骤不能为空")

        recipe_dict = recipe.model_dump()
        db_recipe = Recipe(
            id=str(uuid.uuid4()),
            **recipe_dict,
            author_id=current_user.id
        )
        db.add(db_recipe)
        await db.commit()
        await db.refresh(db_recipe)
        logger.info(f"用户 {current_user.username} 成功创建菜谱: {recipe.title}")
        
        return {
            "schema_version": "1.0",
            "recipe": {
                "id": db_recipe.id,
                "title": db_recipe.title,
                "description": db_recipe.description,
                "ingredients": db_recipe.ingredients,
                "steps": db_recipe.steps,
                "cooking_time": db_recipe.cooking_time,
                "difficulty": db_recipe.difficulty,
                "cuisine_type": db_recipe.cuisine_type,
                "author_id": db_recipe.author_id,
                "created_at": db_recipe.created_at,
                "updated_at": db_recipe.updated_at,
                "views_count": db_recipe.views_count,
                "average_rating": db_recipe.average_rating
            }
        }
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"创建菜谱失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建菜谱失败")

@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取单个菜谱的详细信息
    
    参数:
        recipe_id (str): 菜谱ID
        db (AsyncSession): 数据库会话
        
    返回:
        RecipeResponse: 菜谱详细信息
        
    错误:
        404: 菜谱不存在
        500: 服务器内部错误
    """
    try:
        # 查询菜谱
        query = select(Recipe).where(Recipe.id == recipe_id)
        result = await db.execute(query)
        recipe = result.scalar_one_or_none()
        
        if not recipe:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="菜谱不存在"
            )
            
        # 更新浏览次数
        recipe.views_count = recipe.views_count + 1 if recipe.views_count else 1
        recipe.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(recipe)
        
        # 构造响应
        response_data = RecipeResponse(
            schema_version="1.0",
            recipe=recipe
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"获取菜谱失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取菜谱失败"
        )

@router.get("/", response_model=RecipeListResponse)
async def search_recipes(
    keyword: Optional[str] = None,
    difficulty: Optional[str] = None,
    cuisine_type: Optional[str] = None,
    page: int = Query(1, gt=0),
    per_page: int = Query(20, gt=0, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    搜索菜谱
    """
    try:
        query = select(Recipe)
        
        # 添加过滤条件
        if keyword:
            query = query.where(Recipe.title.ilike(f"%{keyword}%"))
        if difficulty:
            query = query.where(Recipe.difficulty == difficulty)
        if cuisine_type:
            query = query.where(Recipe.cuisine_type == cuisine_type)
            
        # 计算总数
        subquery = query.subquery()
        count_query = select(func.count()).select_from(subquery)
        total = await db.scalar(count_query)
        
        # 分页
        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(query)
        recipes = result.scalars().all()
        
        pagination = PaginationInfo(
            total=total,
            page=page,
            per_page=per_page,
            pages=(total + per_page - 1) // per_page
        )
        
        response_data = RecipeListResponse(
            schema_version="1.0",
            recipes=list(recipes),
            pagination=pagination
        )
        return response_data
        
    except Exception as e:
        await db.rollback()
        logger.error(f"搜索菜谱失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="搜索菜谱失败")

@router.post("/{recipe_id}/rate", response_model=RecipeResponse)
async def rate_recipe(
    recipe_id: str,
    rating: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """为菜谱评分
    
    参数:
        recipe_id (str): 菜谱ID
        rating (RatingCreate): 评分信息，包含评分值和评论
        current_user (User): 当前登录用户
        db (AsyncSession): 数据库会话
        
    返回:
        RecipeResponse: 更新后的菜谱信息
        
    错误:
        404: 菜谱不存在
        400: 已经评分过
        500: 服务器内部错误
    """
    try:
        # 查询菜谱是否存在
        recipe = await db.get(Recipe, recipe_id)
        if not recipe:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="菜谱不存在"
            )
            
        # 检查用户是否已经评分过
        query = select(Rating).where(
            Rating.recipe_id == recipe_id,
            Rating.user_id == current_user.id
        )
        result = await db.execute(query)
        existing_rating = result.scalar_one_or_none()
        
        if existing_rating:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="您已经评分过这个菜谱"
            )
            
        # 创建评分记录
        rating_record = Rating(
            id=str(uuid.uuid4()),
            recipe_id=recipe_id,
            user_id=current_user.id,
            rating=rating.rating,
            comment=rating.comment,
            created_at=datetime.now(UTC)
        )
        db.add(rating_record)
        
        # 更新菜谱的平均评分
        stmt = select(func.avg(Rating.rating)).where(Rating.recipe_id == recipe_id)
        result = await db.execute(stmt)
        avg_rating = result.scalar() or rating.rating
        recipe.average_rating = avg_rating
        recipe.updated_at = datetime.now(UTC)
        
        await db.commit()
        await db.refresh(recipe)
        
        response_data = RecipeResponse(
            schema_version="1.0",
            recipe=recipe
        )
        return response_data
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        logger.error(f"评分失败: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="评分失败"
        )

@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: str,
    recipe_update: RecipeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新菜谱全部信息
    
    参数:
        recipe_id (str): 菜谱ID
        recipe_update (RecipeUpdate): 更新的菜谱信息
        current_user (User): 当前登录用户
        db (AsyncSession): 数据库会话
        
    返回:
        RecipeResponse: 更新后的菜谱信息
        
    错误:
        404: 菜谱不存在
        403: 无权限修改他人的菜谱
        500: 服务器内部错误
    """
    try:
        # 检查菜谱是否存在
        stmt = select(Recipe).where(Recipe.id == recipe_id)
        result = await db.execute(stmt)
        recipe = result.scalar_one_or_none()
        
        if recipe is None:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="菜谱不存在")
            
        # 检查权限
        if recipe.author_id != current_user.id:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="FORBIDDEN"
            )
            
        # 更新菜谱
        update_data = recipe_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(recipe, key, value)
            
        recipe.updated_at = datetime.now(UTC)  # 使用 UTC 时间
        await db.commit()
        await db.refresh(recipe)
        
        response_data = RecipeResponse(schema_version="1.0", recipe=recipe)
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新菜谱失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新菜谱失败")

@router.patch("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: str,
    recipe_update: RecipeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """部分更新菜谱信息
    
    参数:
        recipe_id (str): 菜谱ID
        recipe_update (RecipeUpdate): 需要更新的菜谱字段
        current_user (User): 当前登录用户
        db (AsyncSession): 数据库会话
        
    返回:
        RecipeResponse: 更新后的菜谱信息
        
    错误:
        404: 菜谱不存在
        403: 无权限修改他人的菜谱
        500: 服务器内部错误
    """
    try:
        # 查询菜谱是否存在
        recipe = await db.get(Recipe, recipe_id)
        if not recipe:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="菜谱不存在"
            )
            
        # 检查权限
        if recipe.author_id != current_user.id:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="FORBIDDEN"
            )
            
        # 更新菜谱信息
        update_data = recipe_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:  # 只更新非空字段
                setattr(recipe, field, value)
            
        recipe.updated_at = datetime.now(UTC)  # 使用 UTC 时间
        await db.commit()
        await db.refresh(recipe)
        
        response_data = RecipeResponse(
            schema_version="1.0",
            recipe=recipe
        )
        return response_data
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新菜谱失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新菜谱失败"
        )

@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除菜谱

    参数:
        - recipe_id: 菜谱ID
        - current_user: 当前登录用户
        - db: 数据库会话

    返回:
        - None

    错误:
        - 404: 菜谱不存在
        - 403: 无权限删除他人的菜谱
        - 500: 服务器内部错误
    """
    try:
        # 检查菜谱是否存在
        stmt = select(Recipe).where(Recipe.id == recipe_id)
        result = await db.execute(stmt)
        recipe = result.scalar_one_or_none()
        
        if recipe is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="菜谱不存在")
            
        # 检查权限
        if recipe.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="FORBIDDEN"
            )
            
        # 删除菜谱
        await db.delete(recipe)
        await db.commit()
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除菜谱失败: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除菜谱失败") 