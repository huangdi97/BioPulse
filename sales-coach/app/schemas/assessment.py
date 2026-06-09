"""评估增强数据模型。"""

from pydantic import BaseModel, Field


class FiveDimensionScore(BaseModel):
    """销售对话五维能力评分。"""

    empathy: float = Field(..., ge=0, le=100, description="共情能力")
    data_citation: float = Field(..., ge=0, le=100, description="数据引用")
    closing: float = Field(..., ge=0, le=100, description="收尾推进")
    objection_handling: float = Field(..., ge=0, le=100, description="异议处理")
    compliance: float = Field(..., ge=0, le=100, description="合规表达")


class RadarChartData(BaseModel):
    """五维雷达图数据。"""

    conversation_id: str
    dimensions: FiveDimensionScore
    labels: list[str] = Field(default_factory=lambda: ["共情", "数据引用", "收尾", "异议处理", "合规"])
    values: list[float]
