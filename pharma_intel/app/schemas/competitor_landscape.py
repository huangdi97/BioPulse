"""竞争格局视图数据模型。"""

from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field


class LandscapeDimension(str, Enum):
    PIPELINE_PROGRESS = "PipelineProgress"
    TARGET_COVERAGE = "TargetCoverage"
    INDICATION_COVERAGE = "IndicationCoverage"
    CLINICAL_STAGE = "ClinicalStage"


class LandscapeCompetitor(BaseModel):
    id: str
    name: str
    therapy_area: str
    dimension_scores: Dict[LandscapeDimension, int]


class LandscapeComparison(BaseModel):
    competitors: List[LandscapeCompetitor]


class RadarSeries(BaseModel):
    competitor_id: str
    competitor_name: str
    scores: Dict[LandscapeDimension, int] = Field(..., description="各维度0-100评分")


class RadarData(BaseModel):
    target_id: str
    dimensions: List[LandscapeDimension]
    series: List[RadarSeries]
