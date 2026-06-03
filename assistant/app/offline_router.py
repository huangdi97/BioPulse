from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from assistant.app.services.offline_service import OfflineService
from shared.auth import get_current_user
from shared.base import ApiResponse, success

router = APIRouter(prefix="/offline", tags=["离线模式"])


class QueueChangeRequest(BaseModel):
    """QueueChangeRequest 服务类。"""

    entity_type: str
    entity_id: Optional[int] = None
    action: str
    payload: Dict[str, Any] = {}


@router.get("/status", summary="Get Status by ID")
def get_status(
    service: OfflineService = Depends(),
    current_user: dict = Depends(get_current_user),
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


@router.post("/sync", summary="Trigger Sync")
def trigger_sync(
    limit: int = Query(50, ge=1, le=500),
    service: OfflineService = Depends(),
    current_user: dict = Depends(get_current_user),
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


@router.post("/enable", summary="Enable Offline")
def enable_offline(
    service: OfflineService = Depends(),
    current_user: dict = Depends(get_current_user),
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


@router.post("/disable", summary="Disable Offline")
def disable_offline(
    service: OfflineService = Depends(),
    current_user: dict = Depends(get_current_user),
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


@router.post("/queue", summary="Queue Change")
def queue_change(
    body: QueueChangeRequest,
    service: OfflineService = Depends(),
    current_user: dict = Depends(get_current_user),
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
