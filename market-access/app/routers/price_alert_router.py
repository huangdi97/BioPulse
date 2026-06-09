"""价格变动预警路由。"""

from fastapi import APIRouter

from shared.base import success

from ..schemas.price_alert import AlertConfig, PriceCheckRequest
from ..services.price_alert_service import (
    check_price_threshold,
    configure_alert,
    get_alert_history,
)

router = APIRouter(prefix="/api/price/alert")


@router.get("/list", tags=["价格"])
async def alert_list():
    """查询价格预警历史。"""
    result = await get_alert_history()
    return success(data=result)


@router.post("/config", tags=["价格"])
async def alert_config(config: AlertConfig):
    """配置价格预警规则。"""
    result = await configure_alert(config)
    return success(data=result)


@router.post("/check", tags=["价格"])
async def alert_check(payload: PriceCheckRequest):
    """检查最新价格是否触发预警。"""
    result = await check_price_threshold(payload.product_id, payload.new_price)
    return success(data=result)
