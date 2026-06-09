"""合规培训数据模型。"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TrainingMaterial(BaseModel):
    """待审核培训材料。"""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="material_id")
    title: str
    content: str
    status: str = "pending"


class Violation(BaseModel):
    """合规违规项。"""

    type: str
    description: str
    suggestion: str


class ComplianceCheckResult(BaseModel):
    """合规审核结果。"""

    material_id: str
    passed: bool
    violations: list[Violation] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high"]
