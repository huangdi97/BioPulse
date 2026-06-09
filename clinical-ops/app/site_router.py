"""中心筛选路由。"""

from fastapi import APIRouter, Query

from shared.base import success

from .services.site_service import get_site_detail, search_sites

router = APIRouter(prefix="/api/sites")


@router.get("/search", tags=["中心管理"])
async def search(
    indication: str = Query(..., description="适应症关键词"),
):
    """按适应症搜索临床试验中心。基于论文和知识图谱数据匹配。"""
    result = await search_sites(indication)
    return success(data=result)


@router.get("/{site_id}", tags=["中心管理"])
async def detail(site_id: str):
    """获取临床试验中心详情。返回完整信息、研究者和试验概况。"""
    result = await get_site_detail(site_id)
    return success(data=result)
