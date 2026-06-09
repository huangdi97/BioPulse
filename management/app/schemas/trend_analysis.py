"""同比环比趋势分析数据模型。"""

from pydantic import BaseModel, Field


class TrendDataPoint(BaseModel):
    """单个趋势数据点。"""

    date: str = Field(..., description="周期起始日期")
    metric_name: str = Field(..., description="指标名称")
    value: float = Field(..., description="指标值")
    period_label: str = Field(..., description="周期标签")
    change_pct: float = Field(..., description="同比或环比变化百分比")
