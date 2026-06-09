"""招标价格监控路由。"""

from fastapi import APIRouter, Query

from shared.base import success

from ..services.price_monitor_service import (
    get_centralized_comparison,
    get_price_history,
    get_province_price,
)

router = APIRouter(prefix="/api/price")


@router.get("/province", tags=["价格"])
async def province_price(
    product_id: str = Query(..., description="产品编号"),
    province: str = Query(..., description="省份，如 jiangsu"),
):
    """查询指定省份中标价格。"""
    result = await get_province_price(product_id, province)
    return success(data=result)


@router.get("/history", tags=["价格"])
async def price_history(
    product_id: str = Query(..., description="产品编号"),
):
    """查询产品历史价格序列。"""
    result = await get_price_history(product_id)
    return success(data=result)


@router.get("/centralized", tags=["集采"])
async def centralized_comparison(
    product_id: str = Query(..., description="产品编号"),
    round: int = Query(..., description="集采批次"),
):
    """查询集采批次中选对比。"""
    result = await get_centralized_comparison(product_id, round)
    return success(data=result)
