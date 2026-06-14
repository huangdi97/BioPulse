"""Data models for analyzer module."""

from pydantic import BaseModel


class Analysis(BaseModel):
    cause: str = "unknown"
    severity: str = "low"
    suggestion: str = ""


class Hypothesis(BaseModel):
    id: str = ""
    description: str = ""
    confidence: float = 0.0
    status: str = "pending"
    evidence_for: list[str] = []
    evidence_against: list[str] = []
    type: str = "anomaly_pattern"


class VerificationPlan(BaseModel):
    hypothesis_id: str = ""
    checks: list[dict] = []


class VerificationResult(BaseModel):
    hypothesis_id: str = ""
    confirmed: bool = False
    confidence: float = 0.0
    evidence: list[str] = []
    narrative: str = ""


class RootCauseNarrative(BaseModel):
    root_cause: str = ""
    confidence: float = 0.0
    reasoning_chain: list[str] = []
    falsified_hypotheses: list[str] = []
    confirmed_hypothesis: str = ""
    recommended_action: str = ""
