"""靶点-管线关联图谱数据模型。"""

from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field


class PipelinePhase(str, Enum):
    PHASE1 = "Phase1"
    PHASE2 = "Phase2"
    PHASE3 = "Phase3"
    NDA = "NDA"
    APPROVED = "Approved"


class Target(BaseModel):
    id: str
    name: str
    gene: str
    pathway: str
    disease_area: str
    phase: str
    mechanism: str


class PipelineProduct(BaseModel):
    id: str
    target_id: str
    product_name: str
    company: str
    phase: PipelinePhase
    mechanism: str
    moa: str
    color_code: str
    indication: str = Field(..., description="适应症")


class TargetPipelineTree(BaseModel):
    """按靶点 -> 适应症 -> 产品组织的树状结构。"""

    targets: List[Dict]
