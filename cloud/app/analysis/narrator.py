"""Narrative report generation for verified anomaly analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .verifier import VerificationResult


@dataclass
class Narrative:
    """President-readable three-part root-cause report."""

    discovery: str
    cause: str
    recommendation: str
    data_references: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "discovery": self.discovery,
            "cause": self.cause,
            "recommendation": self.recommendation,
            "data_references": self.data_references,
        }


class Narrator:
    """Turn verification results into a concise natural-language narrative."""

    def generate_narrative(self, verification_result: VerificationResult) -> Narrative:
        """Generate a three-part narrative: discovery, cause, recommendation."""
        result = verification_result
        refs = _refs(result.evidence)
        anomaly_ref = refs[0] if refs else f"verification:{result.anomaly_id}"
        confidence_text = f"{int(result.confidence * 100)}%"

        discovery_sentence = (
            f"发现：系统对异常 {result.anomaly_id} 完成了 {result.rounds} 轮验证，"
            f"当前根因置信度为 {confidence_text}。"
        )
        cause_sentence = f"原因：最可能的根因是{result.root_cause}"
        if result.converged:
            cause_sentence += " 该结论已达到80%置信度收敛条件。"
        else:
            cause_sentence += " 当前证据未完全收敛，但这是已验证候选中置信度最高的解释。"
        recommendation_sentence = f"建议：{result.recommendation}"

        data_references = [
            {"sentence": discovery_sentence, "source": anomaly_ref},
            {"sentence": cause_sentence, "source": refs[1] if len(refs) > 1 else anomaly_ref},
            {"sentence": recommendation_sentence, "source": refs[2] if len(refs) > 2 else anomaly_ref},
        ]
        return Narrative(
            discovery=discovery_sentence,
            cause=cause_sentence,
            recommendation=recommendation_sentence,
            data_references=data_references,
        )


def _refs(evidence: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for item in evidence:
        source = item.get("source") or item.get("data_source") or item.get("ref")
        if source:
            values.append(str(source))
    return values
