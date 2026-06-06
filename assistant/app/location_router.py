"""定位路由模块，定义HCP位置管理与路线优化的 API 端点。"""

from typing import List, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status

from assistant.app.services.location_service import LocationService
from shared.auth import get_current_user
from shared.base import ApiResponse, success

router = APIRouter(tags=["locations", "routes"])


class LocationCreate(BaseModel):
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_primary: Optional[int] = None
    notes: Optional[str] = None


class LocationUpdate(BaseModel):
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_primary: Optional[int] = None
    notes: Optional[str] = None


class LocationOut(BaseModel):
    id: int
    hcp_id: int
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_primary: int
    notes: Optional[str] = None
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RouteRequest(BaseModel):
    start_lat: float
    start_lng: float
    hcp_ids: List[int]
    max_results: Optional[int] = None


class RouteStop(BaseModel):
    hcp_id: int
    hcp_name: str
    address: str
    distance_km: float
    order: int


class RouteResponse(BaseModel):
    optimized_route: List[RouteStop]
    total_distance_km: float
    total_hcps: int


@router.post("/hcp/{hcp_id}/locations")
def create_location(
    hcp_id: int,
    body: LocationCreate,
    service: LocationService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """为指定 HCP 创建地址位置。

    Args:
        hcp_id: HCP ID
        body: 位置创建数据（地址、经纬度等）
        service: 位置服务
        current_user: 当前登录用户

    Returns:
        包含新创建位置的 JSON 响应
    """
    user_id = int(current_user["sub"])
    result = service.create(hcp_id, body, user_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/hcp/{hcp_id}/locations")
def list_locations(
    hcp_id: int,
    service: LocationService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[List[LocationOut]]:
    """获取指定 HCP 的所有地址位置列表。

    Args:
        hcp_id: HCP ID
        service: 位置服务
        current_user: 当前登录用户

    Returns:
        位置列表
    """
    rows = service.list(hcp_id)
    return success(data=[LocationOut(**r) for r in rows])


@router.patch("/locations/{location_id}")
def update_location(
    location_id: int,
    body: LocationUpdate,
    service: LocationService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[LocationOut]:
    """更新指定位置的字段信息。

    Args:
        location_id: 位置 ID
        body: 需要更新的字段数据
        service: 位置服务
        current_user: 当前登录用户

    Returns:
        更新后的位置信息
    """
    updated = service.update(location_id, body)
    return success(data=LocationOut(**updated))


@router.delete("/locations/{location_id}")
def delete_location(
    location_id: int,
    service: LocationService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """删除指定位置。

    Args:
        location_id: 位置 ID
        service: 位置服务
        current_user: 当前登录用户

    Returns:
        成功删除的消息
    """
    service.delete(location_id)
    return success(message="deleted")


@router.post("/routes/optimize")
def optimize_route(
    body: RouteRequest,
    service: LocationService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[RouteResponse]:
    """根据起点和 HCP 列表优化行程路线。

    Args:
        body: 路线请求数据（起点经纬度、HCP ID 列表）
        service: 位置服务
        current_user: 当前登录用户

    Returns:
        优化后的路线及总距离
    """
    data = service.optimize_route(body)
    return success(
        data=RouteResponse(
            optimized_route=[RouteStop(**s) for s in data["optimized_route"]],
            total_distance_km=data["total_distance_km"],
            total_hcps=data["total_hcps"],
        )
    )
