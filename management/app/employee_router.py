"""员工视图路由。提供员工个人资料、任务、合规、绩效和趋势查询。"""

from fastapi import APIRouter, Query

from management.app.services.employee_service import (
    get_my_compliance,
    get_my_performance,
    get_my_profile,
    get_my_tasks,
    get_my_trend,
)
from shared.base import success

router = APIRouter(prefix="/api/employee")


@router.get("/me/profile", summary="个人资料", description="获取当前登录员工的个人资料信息", tags=["团队"])
async def my_profile(user_id: int = Query(..., description="用户 ID")):
    """个人资料。"""
    data = await get_my_profile(user_id)
    return success(data=data)


@router.get("/me/tasks", summary="我的任务", description="获取当前登录员工的任务列表", tags=["团队"])
async def my_tasks(user_id: int = Query(..., description="用户 ID")):
    """我的任务列表。"""
    data = await get_my_tasks(user_id)
    return success(data=data)


@router.get("/me/compliance", summary="合规数据", description="获取当前登录员工的合规执行数据", tags=["团队"])
async def my_compliance(user_id: int = Query(..., description="用户 ID")):
    """我的合规数据。"""
    data = await get_my_compliance(user_id)
    return success(data=data)


@router.get("/me/performance", summary="绩效数据", description="获取当前登录员工的绩效评估数据", tags=["团队"])
async def my_performance(user_id: int = Query(..., description="用户 ID")):
    """我的绩效数据。"""
    data = await get_my_performance(user_id)
    return success(data=data)


@router.get("/me/trend", summary="趋势数据", description="获取当前登录员工的工作趋势分析数据", tags=["团队"])
async def my_trend(user_id: int = Query(..., description="用户 ID")):
    """我的趋势数据。"""
    data = await get_my_trend(user_id)
    return success(data=data)
