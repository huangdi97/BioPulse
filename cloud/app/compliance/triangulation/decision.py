"""Triangulation data types — finding, result & serialisation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# Pattern confidence weights for the triangulation decision chain.
# Each entry maps a pattern name to its base weight used in aggregating
# multi-pattern confidence scores into a final decision.
PATTERN_WEIGHTS: dict[str, float] = {
    "expense_waste": 1.0,
    "visit_fraud": 1.0,
    "channel_stuffing": 1.0,
    "management_neglect": 1.0,
    "fake_activity": 1.0,
    "fake_distribution": 0.9,
}

# Decision thresholds used across all patterns.
RED_LIGHT_THRESHOLD = 0.8
SECONDARY_INVESTIGATION_THRESHOLD = 0.5


@dataclass
class TriangulationFinding:
    """One triangulation anomaly finding."""

    pattern: str
    category: str
    score: float
    confidence: str
    decision: str
    detail: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the finding to a dictionary.

        Args:
            None.

        Returns:
            Dictionary representation of the finding.
        """
        return asdict(self)


@dataclass
class TriangulationResult:
    """Triangulation check result across all detection patterns."""

    passed: bool
    confidence_score: float
    suspicion_level: str
    decision: str
    findings: list[TriangulationFinding] = field(default_factory=list)
    correlated_records: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    recommended_action: str = "pass"
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result to a dictionary.

        Args:
            None.

        Returns:
            Dictionary representation of the result.
        """
        data = asdict(self)
        data["findings"] = [finding.to_dict() for finding in self.findings]
        return data
