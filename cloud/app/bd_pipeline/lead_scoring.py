"""Lead scoring engine — BANT + custom weights."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScoreResult:
    """Result of a lead scoring evaluation."""

    lead_id: str
    total_score: float
    bant_score: float
    custom_score: float
    tier: str  # hot | warm | cold
    breakdown: dict[str, float] = field(default_factory=dict)


BANT_WEIGHTS = {
    "budget": 0.25,
    "authority": 0.25,
    "need": 0.30,
    "timeline": 0.20,
}

DEFAULT_CUSTOM_WEIGHTS = {
    "competitive_intel_match": 0.15,
    "bidding_presence": 0.15,
    "engagement_history": 0.20,
    "hcp_influence": 0.20,
    "market_growth": 0.15,
    "regulatory_approval": 0.15,
}


class LeadScorer:
    """Lead scoring engine using BANT + custom weights."""

    def __init__(self, custom_weights: dict[str, float] | None = None):
        self._custom_weights = custom_weights or DEFAULT_CUSTOM_WEIGHTS

    def score(self, lead_id: str, bant_input: dict[str, float], custom_input: dict[str, float]) -> ScoreResult:
        """Compute lead score from BANT and custom dimensions."""
        bant_score = sum(bant_input.get(k, 0.0) * w for k, w in BANT_WEIGHTS.items())
        custom_score = sum(custom_input.get(k, 0.0) * w for k, w in self._custom_weights.items())
        total = bant_score * 0.6 + custom_score * 0.4
        tier = "hot" if total >= 0.75 else "warm" if total >= 0.45 else "cold"
        return ScoreResult(
            lead_id=lead_id,
            total_score=round(total, 4),
            bant_score=round(bant_score, 4),
            custom_score=round(custom_score, 4),
            tier=tier,
            breakdown={"bant": bant_score, "custom": custom_score, **bant_input, **custom_input},
        )

    def batch_score(self, leads: list[dict[str, Any]]) -> list[ScoreResult]:
        """Score a batch of leads."""
        return [self.score(lead["id"], lead.get("bant", {}), lead.get("custom", {})) for lead in leads]
