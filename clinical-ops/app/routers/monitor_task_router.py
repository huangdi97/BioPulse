"""监查员任务管理路由。"""

from fastapi import APIRouter, Query

from shared.base import success

from ..schemas.monitor_task import MonitorTaskCreate, MonitorTaskUpdate
from ..services.monitor_task_service import (
    create_task,
    get_task_dashboard,
    list_tasks,
    update_task,
)

router = APIRouter(prefix="/api/monitor")


@router.get("/tasks", tags=["监查"])
async def tasks(
    status: str | None = Query(None, description="任务状态"),
    site_id: str | None = Query(None, description="中心编号"),
):
    """查询监查任务列表。"""
    result = await list_tasks(status=status, site_id=site_id)
    return success(data=result)


@router.post("/tasks", tags=["监查"])
async def create(payload: MonitorTaskCreate):
    """创建监查任务。"""
    result = await create_task(payload)
    return success(data=result)


@router.put("/tasks/{id}", tags=["监查"])
async def update(id: str, payload: MonitorTaskUpdate):
    """更新监查任务。"""
    result = await update_task(id, payload)
    return success(data=result)


@router.get("/dashboard", tags=["监查"])
async def dashboard():
    """获取监查任务 dashboard。"""
    result = await get_task_dashboard()
    return success(data=result)
