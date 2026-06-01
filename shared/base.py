from enum import IntEnum
from pydantic import BaseModel
from typing import Generic, List, Optional, TypeVar


class ErrorCode(IntEnum):
    """Standardized error codes for API responses."""

    SUCCESS = 0
    UNAUTHORIZED = 1
    FORBIDDEN = 2
    NOT_FOUND = 3
    VALIDATION_ERROR = 4
    INTERNAL_ERROR = 5
    CONFLICT = 6
    RATE_LIMITED = 7


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Generic API response wrapper."""

    code: ErrorCode = ErrorCode.SUCCESS
    message: str = "ok"
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


def success(data: T = None, message: str = "ok") -> ApiResponse[T]:
    """Create a success response.

    Args:
        data: Response payload.
        message: Success message.

    Returns:
        ApiResponse with SUCCESS code.
    """
    return ApiResponse(data=data, message=message)


def error(code: ErrorCode, message: str) -> ApiResponse:
    """Create an error response.

    Args:
        code: Error code.
        message: Error description.

    Returns:
        ApiResponse with the given error code.
    """
    return ApiResponse(code=code, message=message)


# === SQL注入防护：列名白名单校验 ===
VALIDATE_COLUMNS_ENABLED = True


def validate_columns(updates: dict, table_name: str, allowed: frozenset) -> None:
    """校验更新dict的key是否都在允许的列名集合中。

    Args:
        updates: 待校验的 {column_name: value} 字典
        table_name: 表名（仅用于错误消息）
        allowed: 该表允许的列名 frozenset

    Raises:
        ValueError: 如果存在不在allowed中的key
    """
    if not VALIDATE_COLUMNS_ENABLED:
        return
    unknown = [k for k in updates if k not in allowed]
    if unknown:
        raise ValueError(
            f"Invalid columns for {table_name}: {unknown}. Allowed: {sorted(allowed)}"
        )
