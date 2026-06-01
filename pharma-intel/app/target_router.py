from fastapi import APIRouter, Query
from pharma_intel.app.services.target_service import (
    analyze_target,
    trending_targets,
)
from shared.base import success

router = APIRouter(prefix="/api/target", tags=["靶点研究监控"])


@router.get("/analyze")
async def target_analyze(
    target: str = Query(..., description="靶点名称，如 PD-1、EGFR"),
):
    """分析指定靶点的学术研究态势。返回论文总数、月度发文趋势、TOP10机构、相关公司。"""
    result = await analyze_target(target)
    return success(data=result)


@router.get("/trending")
async def trending_targets_endpoint(
    limit: int = Query(10, ge=1, le=30),
):
    """获取近期活跃靶点列表。返回近期发文量最多的靶点排名。"""
    result = await trending_targets(limit)
    return success(data=result)
