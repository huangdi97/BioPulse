"""准入策略推演路由。"""

from fastapi import APIRouter, Query
from market_access.app.services.strategy_service import (
    get_access_strategy,
    get_competitor_landscape,
    get_policy_news,
)

from shared.base import success

router = APIRouter(prefix="/api/strategy", tags=["准入策略"])


@router.get("/access")
async def access_strategy(
    drug_name: str = Query(..., description="药品名称"),
    target_province: str = Query(..., description="目标省份"),
):
    """生成药品准入策略建议。基于医保状态、招标信息和竞品情报综合分析。"""
    result = await get_access_strategy(drug_name, target_province)
    return success(data=result)


@router.get("/landscape")
async def competitor_landscape(
    drug_name: str = Query(..., description="药品名称"),
):
    """查询竞品准入 landscape。返回竞品列表、准入状态等。"""
    result = await get_competitor_landscape(drug_name)
    return success(data=result)


@router.get("/policy-news")
async def policy_news():
    """获取医药政策动态。返回最新政策新闻列表。"""
    result = await get_policy_news()
    return success(data=result)
