from fastapi import APIRouter, Query

from pharma_intel.app.services.kol_service import search_kol
from shared.base import success

router = APIRouter(prefix="/api/kol", tags=["KOL学术影响力"])


@router.get("/search")
async def search_kol_endpoint(
    name: str = Query(..., description="KOL 姓名"),
    institution: str = Query("", description="所属机构"),
):
    """搜索 KOL 学术画像。返回论文数、研究领域、活跃年份、H指数。"""
    result = await search_kol(name, institution)
    return success(data=result)


@router.get("/trending")
async def trending_kols(
    limit: int = Query(10, ge=1, le=50),
):
    """获取近期活跃 KOL 列表。"""
    # 当前简化版本返回说明
    return success(
        data={
            "message": "Trending KOLs feature requires full PubMed integration. Use /api/kol/search?name=... for individual KOL search.",
            "limit": limit,
        }
    )
