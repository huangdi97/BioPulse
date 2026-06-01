"""招标价格监控路由。"""

from fastapi import APIRouter, Query
from market_access.app.services.bidding_service import (
    get_bidding_data,
    get_price_trend,
    get_province_prices,
)

from shared.base import success

router = APIRouter(prefix="/api/bidding", tags=["招标监控"])


@router.get("/price")
async def bidding_price(
    drug_name: str = Query(..., description="药品名称"),
):
    """查询药品招标价格信息。返回招标新闻/情报列表。"""
    result = await get_bidding_data(drug_name)
    return success(data=result)


@router.get("/trend")
async def price_trend(
    drug_name: str = Query(..., description="药品名称"),
):
    """获取药品近 6 个月价格趋势。返回月度价格序列。"""
    result = await get_price_trend(drug_name)
    return success(data=result)


@router.get("/provinces")
async def province_prices(
    drug_name: str = Query(..., description="药品名称"),
):
    """查询各省药品中标价。返回省份及对应中标价格列表。"""
    result = await get_province_prices(drug_name)
    return success(data=result)
