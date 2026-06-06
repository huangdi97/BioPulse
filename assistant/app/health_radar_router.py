"""健康雷达路由模块，定义健康评估记录的 API 端点。"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from starlette import status

from assistant.app.services.health_radar_service import HealthRadarService
from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success

router = APIRouter(prefix="/health-radar", tags=["health-radar"])


class HealthRadarCreate(BaseModel):
    patient_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    diagnosis: Optional[str] = None
    risk_factors: Optional[str] = None
    medication_history: Optional[str] = None
    score: Optional[int] = 50
    assessment_date: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("score")
    @classmethod
    def score_range(cls, v: Optional[int]) -> Optional[int]:
        """校验评分范围（0-100）。"""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("score must be between 0 and 100")
        return v


class HealthRadarUpdate(BaseModel):
    patient_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    diagnosis: Optional[str] = None
    risk_factors: Optional[str] = None
    medication_history: Optional[str] = None
    score: Optional[int] = None
    assessment_date: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[int] = None

    @field_validator("score")
    @classmethod
    def score_range(cls, v: Optional[int]) -> Optional[int]:
        """校验评分范围（0-100）。"""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("score must be between 0 and 100")
        return v


class HealthRadarOut(BaseModel):
    id: int
    patient_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    diagnosis: Optional[str] = None
    risk_factors: Optional[str] = None
    medication_history: Optional[str] = None
    score: int
    assessment_date: Optional[str] = None
    notes: Optional[str] = None
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("")
def create_health_radar(
    body: HealthRadarCreate,
    service: HealthRadarService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """创建健康雷达记录。

    Args:
        body: 健康雷达创建数据（患者姓名、评分等）
        service: 健康雷达服务
        current_user: 当前登录用户

    Returns:
        包含新创建记录的 JSON 响应
    """
    user_id = int(current_user["sub"])
    result = service.create(body, user_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("")
def list_health_radar(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_name: Optional[str] = Query(None),
    score_min: Optional[int] = Query(None),
    score_max: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    service: HealthRadarService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[HealthRadarOut]]:
    """分页查询健康雷达记录列表，支持按患者姓名、评分范围、日期范围筛选。

    Args:
        page: 页码（从1开始）
        page_size: 每页数量
        patient_name: 患者姓名（可选筛选）
        score_min: 最低评分（可选筛选）
        score_max: 最高评分（可选筛选）
        date_from: 开始日期（可选筛选）
        date_to: 结束日期（可选筛选）
        service: 健康雷达服务
        current_user: 当前登录用户

    Returns:
        分页的健康雷达记录列表
    """
    total, total_pages, rows = service.list(page, page_size, patient_name, score_min, score_max, date_from, date_to)
    items = [HealthRadarOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/stats")
def get_health_radar_stats(
    service: HealthRadarService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict]:
    """获取健康雷达统计信息（如总记录数、评分分布等）。

    Args:
        service: 健康雷达服务
        current_user: 当前登录用户

    Returns:
        统计数据的字典
    """
    data = service.get_stats()
    return success(data=data)


@router.get("/{health_radar_id}")
def get_health_radar(
    health_radar_id: int,
    service: HealthRadarService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[HealthRadarOut]:
    """获取指定健康雷达记录的详细信息。

    Args:
        health_radar_id: 健康雷达记录 ID
        service: 健康雷达服务
        current_user: 当前登录用户

    Returns:
        健康雷达记录详情
    """
    row = service.get(health_radar_id)
    return success(data=HealthRadarOut(**row))


@router.patch("/{health_radar_id}")
def update_health_radar(
    health_radar_id: int,
    body: HealthRadarUpdate,
    service: HealthRadarService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[HealthRadarOut]:
    """更新指定健康雷达记录的部分字段。

    Args:
        health_radar_id: 健康雷达记录 ID
        body: 需要更新的字段数据
        service: 健康雷达服务
        current_user: 当前登录用户

    Returns:
        更新后的健康雷达记录
    """
    updated = service.update(health_radar_id, body)
    return success(data=HealthRadarOut(**updated))


@router.delete("/{health_radar_id}")
def delete_health_radar(
    health_radar_id: int,
    service: HealthRadarService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """删除指定健康雷达记录。

    Args:
        health_radar_id: 健康雷达记录 ID
        service: 健康雷达服务
        current_user: 当前登录用户

    Returns:
        成功删除的消息
    """
    service.delete(health_radar_id)
    return success(message="deleted")
