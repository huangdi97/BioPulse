"""招标价格监控数据模型。"""

from datetime import date as Date

from pydantic import BaseModel, Field


class ProvincePrice(BaseModel):
    product_id: str = Field(..., description="产品编号")
    province: str = Field(..., description="省份")
    winning_price: float = Field(..., description="中标价")
    bid_date: Date = Field(..., description="中标日期")
    procurement_volume: int = Field(..., description="采购量")
    manufacturer: str = Field(..., description="生产企业")


class PricePoint(BaseModel):
    date: Date = Field(..., description="价格日期")
    price: float = Field(..., description="价格")
    source: str = Field(..., description="数据来源")


class PriceHistory(BaseModel):
    product_id: str = Field(..., description="产品编号")
    province: str = Field(..., description="省份")
    price_series: list[PricePoint] = Field(default_factory=list, description="价格序列")
    volatility: float = Field(..., description="波动率")


class CentralizedProcurement(BaseModel):
    round: int = Field(..., description="集采批次")
    products: list[str] = Field(default_factory=list, description="纳入产品")
    winning_companies: list[str] = Field(default_factory=list, description="中选企业")
    price_reduction_rate: float = Field(..., description="平均降幅")
