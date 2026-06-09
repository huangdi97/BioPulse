"""价格变动预警数据模型。"""

from datetime import datetime

from pydantic import BaseModel, Field


class PriceAlert(BaseModel):
    product_id: str = Field(..., description="产品编号")
    old_price: float = Field(..., description="原价格")
    new_price: float = Field(..., description="新价格")
    change_pct: float = Field(..., description="变动比例")
    threshold: float = Field(..., description="预警阈值")
    trigger_time: datetime = Field(..., description="触发时间")
    severity: str = Field(..., description="预警等级")


class AlertConfig(BaseModel):
    user_id: str = Field(..., description="用户编号")
    product_ids: list[str] = Field(default_factory=list, description="关注产品")
    threshold_pct: float = Field(5.0, description="变动阈值百分比")
    notify_channels: list[str] = Field(default_factory=list, description="通知渠道")


class PriceCheckRequest(BaseModel):
    product_id: str = Field(..., description="产品编号")
    new_price: float = Field(..., gt=0, description="最新价格")
