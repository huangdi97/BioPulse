"""数据同步路由模块，定义客户端数据推送、拉取与状态查询的 API 端点。"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from assistant.app.services.sync_service import SyncService
from shared.auth import get_current_user
from shared.base import ApiResponse, success

router = APIRouter(prefix="/sync", tags=["sync"])


class SyncOperation(BaseModel):
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    payload: Dict[str, Any]
    client_created_at: str


class SyncPushRequest(BaseModel):
    client_id: str
    operations: List[SyncOperation]


class SyncPushResult(BaseModel):
    operation_id: int
    status: str
    server_entity_id: Optional[int] = None


class SyncPushResponse(BaseModel):
    synced: int
    failed: int
    server_operations: List[SyncPushResult]


@router.post("/push")
def sync_push(
    body: SyncPushRequest,
    service: SyncService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[SyncPushResponse]:
    """将客户端离线操作推送到服务端进行同步。

    Args:
        body: 同步推送请求（客户端 ID 和操作列表）
        service: 同步服务
        current_user: 当前登录用户

    Returns:
        同步结果（成功/失败数量及服务端操作结果）
    """
    user_id = int(current_user["sub"])
    data = service.push(body, user_id)
    return success(
        data=SyncPushResponse(
            synced=data["synced"],
            failed=data["failed"],
            server_operations=[SyncPushResult(**r) for r in data["server_operations"]],
        )
    )


@router.get("/pull")
def sync_pull(
    since: str = Query(...),
    service: SyncService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """从服务端拉取自指定时间以来发生变更的数据。

    Args:
        since: 起始时间（ISO 格式字符串）
        service: 同步服务
        current_user: 当前登录用户

    Returns:
        变更数据
    """
    data = service.pull(since)
    return success(data=data)


@router.get("/status")
def sync_status(
    service: SyncService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """获取当前同步状态信息（如待同步操作数量等）。

    Args:
        service: 同步服务
        current_user: 当前登录用户

    Returns:
        同步状态数据
    """
    data = service.get_status()
    return success(data=data)
