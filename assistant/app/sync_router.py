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
    data = service.pull(since)
    return success(data=data)


@router.get("/status")
def sync_status(
    service: SyncService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    data = service.get_status()
    return success(data=data)
