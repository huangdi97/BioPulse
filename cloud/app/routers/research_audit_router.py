"""科研审计路由：审计日志查询与模式切换记录。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from starlette import status

from cloud.app.services.research_audit_service import (
    get_audit_log,
    get_audit_logs,
    get_audit_logs_by_type,
    record_switch,
)
from shared.auth import get_current_user
from shared.auth_scope import require_scope

router = APIRouter(
    prefix="/api/research/audit",
    tags=["科研线"],
    dependencies=[Depends(require_scope("research"))],
)


class SwitchRequest(BaseModel):
    """模式切换记录请求体。"""

    from_mode: str
    to_mode: str
    device_id: str = ""
    gps: str = ""


@router.get("/logs", summary="审计日志列表", description="分页查询科研审计日志")
def list_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    logs = get_audit_logs(page=page, per_page=per_page)
    return {"code": 0, "data": logs, "message": "success"}


@router.get("/logs/{log_id}", summary="审计日志详情", description="根据ID查询单条审计日志的详细信息")
def get_log(
    log_id: int,
    current_user: dict = Depends(get_current_user),
):
    log = get_audit_log(log_id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
    return {"code": 0, "data": log, "message": "success"}


@router.get("/logs/by-type/{event_type}", summary="按类型查询审计日志", description="根据事件类型过滤审计日志")
def list_logs_by_type(
    event_type: str,
    current_user: dict = Depends(get_current_user),
):
    logs = get_audit_logs_by_type(event_type)
    return {"code": 0, "data": logs, "message": "success"}


@router.post("/switch", status_code=201, summary="记录模式切换", description="记录科研模式之间的切换操作")
def switch_mode(
    body: SwitchRequest,
    current_user: dict = Depends(get_current_user),
):
    operator = current_user.get("username", "")
    record_switch(
        from_mode=body.from_mode,
        to_mode=body.to_mode,
        operator=operator,
        device_id=body.device_id,
        gps=body.gps,
    )
    return {"code": 0, "message": "switch logged"}
