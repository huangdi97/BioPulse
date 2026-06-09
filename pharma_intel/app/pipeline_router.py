"""管线竞争分析路由。提供按公司/适应症查询管线及活跃管线列表。"""

from fastapi import APIRouter, Query

from pharma_intel.app.services.pipeline_service import (
    analyze_pipeline,
    search_pipeline_by_indication,
)
from shared.base import success

router = APIRouter(prefix="/api/pipeline")


@router.get("/by-company", tags=["管线"])
async def pipeline_by_company(
    company: str = Query(..., description="公司名称"),
    therapeutic_area: str = Query("", description="治疗领域"),
):
    """按公司及治疗领域分析管线。返回管线总数、分期分布、适应症分布、TOP5竞争对手。"""
    result = await analyze_pipeline(company, therapeutic_area)
    return success(data=result)


@router.get("/by-indication", tags=["管线"])
async def pipeline_by_indication(
    indication: str = Query(..., description="适应症名称"),
):
    """按适应症搜索在研管线。返回匹配该适应症的管线列表及相关信息。"""
    result = await search_pipeline_by_indication(indication)
    return success(data=result)


@router.get("/trending", tags=["管线"])
async def trending_pipelines(
    limit: int = Query(10, ge=1, le=50),
):
    """获取近期活跃管线列表。当前简化版本返回说明信息。"""
    return success(
        data={
            "message": "Trending pipelines feature requires full KG integration. "
            "Use /api/pipeline/by-company or /api/pipeline/by-indication for targeted search.",
            "limit": limit,
        }
    )
