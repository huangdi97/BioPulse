"""离线模式路由模块，定义离线状态的切换与离线同步队列的 API 端点。"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from assistant.app.services.offline_service import OfflineService
from shared.auth_scope import require_scope
from shared.base import ApiResponse, success

router = APIRouter(prefix="/offline")


class QueueChangeRequest(BaseModel):
    """QueueChangeRequest 服务类。"""

    entity_type: str
    entity_id: Optional[int] = None
    action: str
    payload: Dict[str, Any] = {}


@router.get("/status", summary="获取离线状态", description="获取当前离线模式的状态信息。", tags=["离线同步"])
def get_status(
    service: OfflineService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """获取状态。

    Args:
        service: 描述
        current_user: 描述

    Returns:
        描述
    """
    data = service.get_status()
    return success(data=data)


@router.post("/sync", summary="触发同步", description="触发离线数据同步到服务器。", tags=["离线同步"])
def trigger_sync(
    limit: int = Query(50, ge=1, le=500),
    service: OfflineService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """trigger_sync 操作。

    Args:
        limit: 描述
        service: 描述
        current_user: 描述

    Returns:
        描述
    """
    data = service.sync_pending(limit=limit)
    return success(data=data)


@router.post("/enable", summary="开启离线模式", description="开启客户端的离线模式功能。", tags=["离线同步"])
def enable_offline(
    service: OfflineService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """enable_offline 操作。

    Args:
        service: 描述
        current_user: 描述

    Returns:
        描述
    """
    data = service.enable_offline_mode()
    return success(data=data)


@router.post("/disable", summary="关闭离线模式", description="关闭离线模式并恢复在线模式。", tags=["离线同步"])
def disable_offline(
    service: OfflineService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """disable_offline 操作。

    Args:
        service: 描述
        current_user: 描述

    Returns:
        描述
    """
    data = service.enable_online_mode()
    return success(data=data)


@router.post("/queue", summary="入队变更", description="将数据变更操作加入离线同步队列。", tags=["离线同步"])
def queue_change(
    body: QueueChangeRequest,
    service: OfflineService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
) -> ApiResponse:
    """入队变更。

    Args:
        service: 描述
        current_user: 描述

    Returns:
        描述
    """
    data = service.queue_change(
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        action=body.action,
        payload=body.payload,
    )
    return success(data=data)
