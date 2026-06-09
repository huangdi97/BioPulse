"""HCP influence scoring schemas."""

from pydantic import BaseModel, Field


class HCPScore(BaseModel):
    hcp_id: str
    prescription_volume: float = Field(..., ge=0, le=100)
    academic_influence: float = Field(..., ge=0, le=100)
    network_score: float = Field(..., ge=0, le=100)
    overall_score: float = Field(..., ge=0, le=100)


class ScoreBreakdown(BaseModel):
    hcp_id: str
    dimensions: dict[str, float]
    weights: dict[str, float]
    weighted_scores: dict[str, float]
    overall_score: float = Field(..., ge=0, le=100)
