"""
ApiResponse
"""

from typing import Any, Generic, TypeVar, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    """所有业务 Schema 的公共基类，统一驼峰转换与全局规则"""
    model_config = ConfigDict(
        alias_generator=to_camel, # 自动转小驼峰
        populate_by_name=True,    # 下划线/驼峰双命名兼容
        extra="forbid",           # 禁止传入未定义字段
    )


class ErrorResponse(BaseSchema):
    """统一错误响应模型"""
    code: str = Field(
        description="业务错误码，语义化字符串，如 UNAUTHORIZED"
    )

    message: str = Field(
        description="人类可读的错误提示文案"
    )

    details: Optional[dict[str, Any]] = Field(
        description="附加详情，存放扩展上下文",
        default=None
    )

    request_id: Optional[str] = Field(
        description="请求追踪ID",
        default=None
    )


# 泛型类型变量，代表任意业务数据类型
Data = TypeVar("Data")

class ApiResponse(BaseSchema, Generic[Data]):
    """统一响应外壳模型"""
    data: Optional[Data] = Field(
        description="业务数据",
        default=None
    )

    meta: Optional[dict[str, Any]] = Field(
        description="元数据",
        default=None
    )
