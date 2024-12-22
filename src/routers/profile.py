from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List
from ..database import get_db
from ..models.user import User
from ..auth.jwt import get_current_active_user
from ..validators import UserProfileInput
import logging
from datetime import datetime

# 创建路由器
router = APIRouter(
    prefix="/profile",
    tags=["用户画像"],
    responses={404: {"description": "未找到"}},
)

@router.get("/me")
async def get_profile(
    current_user: User = Depends(get_current_active_user)
) -> Dict:
    """获取当前用户画像
    
    返回当前登录用户的完整画像信息
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        Dict: 用户画像数据
    """
    return current_user.profile or {}

@router.put("/me")
async def update_profile(
    profile_data: UserProfileInput,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict:
    """更新用户画像
    
    更新当前用户的画像信息
    
    Args:
        profile_data: 新的画像数据
        current_user: 当前用户对象
        db: 数据库会话
        
    Returns:
        Dict: 更新后的画像数据
        
    Raises:
        HTTPException: 当更新失败时抛出
    """
    try:
        # 更新画像数据
        current_user.update_profile(profile_data.dict(exclude_unset=True))
        db.commit()
        
        return current_user.profile
        
    except Exception as e:
        db.rollback()
        logging.error(f"更新用户画像失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新画像失败，请稍后重试"
        )

@router.post("/preferences")
async def set_preferences(
    preferences: Dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict:
    """设置用户偏好
    
    更新用户的偏好设置
    
    Args:
        preferences: 偏好设置数据
        current_user: 当前用户对象
        db: 数据库会话
        
    Returns:
        Dict: 更新后的偏好设置
    """
    try:
        if not current_user.profile:
            current_user.profile = {}
        current_user.profile["preferences"] = preferences
        db.commit()
        
        return current_user.profile["preferences"]
        
    except Exception as e:
        db.rollback()
        logging.error(f"设置用户偏好失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="设置偏好失败，请稍后重试"
        )

@router.post("/dietary-restrictions")
async def set_dietary_restrictions(
    restrictions: List[str],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[str]:
    """设置饮食限制
    
    更新用户的饮食限制信息
    
    Args:
        restrictions: 饮食限制列表
        current_user: 当前用户对象
        db: 数据库会话
        
    Returns:
        List[str]: 更新后的饮食限制列表
    """
    try:
        if not current_user.profile:
            current_user.profile = {}
        current_user.profile["dietary_restrictions"] = restrictions
        db.commit()
        
        return current_user.profile["dietary_restrictions"]
        
    except Exception as e:
        db.rollback()
        logging.error(f"设置饮食限制失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="设置饮食限制失败，请稍后重试"
        )

@router.post("/health-goals")
async def set_health_goals(
    goals: List[str],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[str]:
    """设置健康目标
    
    更新用户的健康目标
    
    Args:
        goals: 健康目标列表
        current_user: 当前用户对象
        db: 数据库会话
        
    Returns:
        List[str]: 更新后的健康目标列表
    """
    try:
        if not current_user.profile:
            current_user.profile = {}
        current_user.profile["health_goals"] = goals
        db.commit()
        
        return current_user.profile["health_goals"]
        
    except Exception as e:
        db.rollback()
        logging.error(f"设置健康目标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="设置健康目标失败，请稍后重试"
        )

@router.post("/cooking-skill")
async def set_cooking_skill(
    skill_level: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> str:
    """设置烹饪技能等级
    
    更新用户的烹饪技能水平
    
    Args:
        skill_level: 技能等级（beginner/intermediate/advanced）
        current_user: 当前用户对象
        db: 数据库会话
        
    Returns:
        str: 更新后的技能等级
        
    Raises:
        HTTPException: 当技能等级无效时抛出
    """
    valid_levels = {"beginner", "intermediate", "advanced"}
    if skill_level not in valid_levels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的技能等级"
        )
    
    try:
        if not current_user.profile:
            current_user.profile = {}
        current_user.profile["cooking_skill"] = skill_level
        db.commit()
        
        return current_user.profile["cooking_skill"]
        
    except Exception as e:
        db.rollback()
        logging.error(f"设置烹饪技能失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="设置烹饪技能失败，请稍后重试"
        )

@router.get("/recommendations")
async def get_recommendations(
    current_user: User = Depends(get_current_active_user)
) -> List[Dict]:
    """获取个性化推荐
    
    基于用户画像生成菜谱推荐
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        List[Dict]: 推荐的菜谱列表
    """
    # TODO: 实现基于用户画像的推荐算法
    return []

@router.post("/feedback")
async def submit_feedback(
    recipe_id: str,
    feedback: Dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict:
    """提交反馈
    
    记录用户对菜谱的反馈
    
    Args:
        recipe_id: 菜谱ID
        feedback: 反馈数据
        current_user: 当前用户对象
        db: 数据库会话
        
    Returns:
        Dict: 提交响应
    """
    try:
        if not current_user.profile:
            current_user.profile = {}
        if "feedback" not in current_user.profile:
            current_user.profile["feedback"] = {}
            
        current_user.profile["feedback"][recipe_id] = {
            "content": feedback,
            "timestamp": str(datetime.now())
        }
        db.commit()
        
        return {"message": "反馈提交成功"}
        
    except Exception as e:
        db.rollback()
        logging.error(f"提交反馈失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="提交反馈失败，请稍后重试"
        ) 