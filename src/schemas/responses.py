from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, Any, Dict
from pydantic.generics import GenericModel
from datetime import datetime

T = TypeVar('T')

class StandardResponse(GenericModel, Generic[T]):
    """标准响应模型
    
    用于统一API响应格式的Pydantic模型，支持泛型数据类型
    """
    
    success: bool = Field(
        ...,
        description="操作是否成功"
    )
    
    message: str = Field(
        ...,
        description="响应消息"
    )
    
    data: Optional[T] = Field(
        None,
        description="响应数据"
    )
    
    error_code: Optional[str] = Field(
        None,
        description="错误代码，仅在失败时返回"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="响应元数据，包含处理时间、请求信息等"
    )

class PaginatedResponse(StandardResponse[T]):
    """分页响应模型
    
    继承自标准响应模型，添加分页相关字段
    """
    
    class PaginationInfo(BaseModel):
        """分页信息模型"""
        current_page: int = Field(
            ...,
            description="当前页码",
            ge=1
        )
        
        page_size: int = Field(
            ...,
            description="每页数量",
            gt=0
        )
        
        total_pages: int = Field(
            ...,
            description="总页数",
            ge=0
        )
        
        total_items: int = Field(
            ...,
            description="总条目数",
            ge=0
        )
        
        has_next: bool = Field(
            ...,
            description="是否有下一页"
        )
        
        has_prev: bool = Field(
            ...,
            description="是否有上一页"
        )
    
    pagination: Optional[PaginationInfo] = Field(
        None,
        description="分页信息"
    )

class ErrorResponse(StandardResponse[None]):
    """错误响应模型
    
    用于返回错误信息的标准格式
    """
    
    success: bool = Field(
        False,
        description="操作失败标志"
    )
    
    error_code: str = Field(
        ...,
        description="错误代码"
    )
    
    error_details: Optional[Any] = Field(
        None,
        description="详细错误信息"
    )
    
    stack_trace: Optional[str] = Field(
        None,
        description="堆栈跟踪信息（仅在开发环境返回）"
    )

class ValidationErrorResponse(ErrorResponse):
    """验证错误响应模型
    
    用于返回数据验证错误的详细信息
    """
    
    error_code: str = Field(
        "VALIDATION_ERROR",
        description="验证错误代码"
    )
    
    field_errors: Dict[str, Any] = Field(
        ...,
        description="字段验证错误详情"
    )

class SuccessResponse(StandardResponse[None]):
    """成功响应模型
    
    用于返回简单的成功消息
    """
    
    success: bool = Field(
        True,
        description="操作成功标志"
    )
    
    message: str = Field(
        "操作成功",
        description="成功消息"
    )

def create_response(
    data: Optional[Any] = None,
    message: str = "操作成功",
    success: bool = True,
    error_code: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict:
    """创建标准响应
    
    Args:
        data: 响应数据
        message: 响应消息
        success: 是否成功
        error_code: 错误代码
        metadata: 元数据
        
    Returns:
        Dict: 标准响应字典
    """
    response = {
        "success": success,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    if error_code:
        response["error_code"] = error_code
    
    if metadata:
        response["metadata"] = metadata
    
    return response

def create_error_response(
    message: str,
    error_code: str,
    error_details: Optional[Any] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict:
    """创建错误响应
    
    Args:
        message: 错误消息
        error_code: 错误代码
        error_details: 错误详情
        metadata: 元数据
        
    Returns:
        Dict: 错误响应字典
    """
    return create_response(
        message=message,
        success=False,
        error_code=error_code,
        metadata={
            **(metadata or {}),
            "error_details": error_details
        }
    )

def create_validation_error_response(
    message: str,
    field_errors: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> Dict:
    """创建验证错误响应
    
    Args:
        message: 错误消息
        field_errors: 字段错误详情
        metadata: 元数据
        
    Returns:
        Dict: 验证错误响应字典
    """
    return create_error_response(
        message=message,
        error_code="VALIDATION_ERROR",
        error_details={"field_errors": field_errors},
        metadata=metadata
    )

def create_success_response(
    message: str = "操作成功",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict:
    """创建简单成功响应
    
    Args:
        message: 成功消息
        metadata: 元数据
        
    Returns:
        Dict: 成功响应字典
    """
    return create_response(
        message=message,
        success=True,
        metadata=metadata
    ) 