"""Cross-representative anomaly pattern discovery."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

HistoryProvider = Callable[[dict[str, Any]], Iterable[dict[str, Any]]]


@dataclass
class RelatedPattern:
    """A historical anomaly related to the current anomaly."""

    pattern_id: str
    anomaly_id: str
    similarity: float
    matched_dimensions: list[str]
    escalation: str
    summary: str
    source: str = "historical_anomalies"
    evidence: dict[str, Any] = field(default_factory=dict)


class PatternDiscovery:
    """Discover similar anomaly patterns across representatives and dealers."""

    def __init__(self, history_provider: HistoryProvider | None = None, min_similarity: float = 0.55):
        self._history_provider = history_provider
        self._min_similarity = min_similarity

    def discover(self, current_anomaly: Any) -> list[RelatedPattern]:
        """Scan historical anomalies and return similar patterns."""
        current = _as_dict(current_anomaly)
        history = list(self._load_history(current))
        patterns = []
        for index, candidate in enumerate(history):
            candidate = _as_dict(candidate)
            if not candidate:
                continue
            similarity, dimensions = _similarity(current, candidate)
            if similarity < self._min_similarity:
                continue
            patterns.append(self._pattern(current, candidate, index, similarity, dimensions))
        return sorted(patterns, key=lambda item: item.similarity, reverse=True)

    def _load_history(self, current: dict[str, Any]) -> Iterable[dict[str, Any]]:
        if self._history_provider:
            return self._history_provider(current)
        evidence = current.get("evidence") if isinstance(current.get("evidence"), dict) else {}
        for key in ("historical_anomalies", "related_events", "history"):
            value = current.get(key, evidence.get(key))
            if isinstance(value, list):
                return value
        return []

    def _pattern(
        self,
        current: dict[str, Any],
        candidate: dict[str, Any],
        index: int,
        similarity: float,
        dimensions: list[str],
    ) -> RelatedPattern:
        current_rep = _value(current, "agent_id", "rep_id", "representative_id")
        candidate_rep = _value(candidate, "agent_id", "rep_id", "representative_id")
        escalation = "single_rep_repeat"
        if "dealer" in dimensions and current_rep and candidate_rep and current_rep != candidate_rep:
            escalation = "dealer_pattern"
        elif "region" in dimensions and current_rep != candidate_rep:
            escalation = "regional_pattern"
        summary = _summary(escalation, dimensions, candidate)
        anomaly_id = str(_value(candidate, "event_id", "anomaly_id", "id") or f"history-{index}")
        return RelatedPattern(
            pattern_id=f"{current.get('event_id') or current.get('anomaly_id') or 'current'}:{anomaly_id}",
            anomaly_id=anomaly_id,
            similarity=round(similarity, 2),
            matched_dimensions=dimensions,
            escalation=escalation,
            summary=summary,
            evidence=candidate,
        )


def _similarity(current: dict[str, Any], candidate: dict[str, Any]) -> tuple[float, list[str]]:
    weights = {
        "dealer": 0.35,
        "rule": 0.22,
        "category": 0.18,
        "product": 0.12,
        "region": 0.1,
        "rep": 0.08,
    }
    dimensions: list[str] = []
    score = 0.0
    comparisons = {
        "dealer": (("dealer_id", "dealer", "distributor_id", "distributor"),),
        "rule": (("rule_code", "rule_id", "violation_code"),),
        "category": (("root_cause_category", "category", "type"),),
        "product": (("product_id", "product", "sku"),),
        "region": (("region", "province", "city"),),
        "rep": (("agent_id", "rep_id", "representative_id"),),
    }
    for dimension, key_groups in comparisons.items():
        keys = key_groups[0]
        if _same_value(current, candidate, keys):
            score += weights[dimension]
            dimensions.append(dimension)
    return min(1.0, score), dimensions


def _same_value(left: dict[str, Any], right: dict[str, Any], keys: tuple[str, ...]) -> bool:
    left_value = _value(left, *keys)
    right_value = _value(right, *keys)
    return bool(left_value and right_value and str(left_value).lower() == str(right_value).lower())


def _value(data: dict[str, Any], *keys: str) -> Any:
    evidence = data.get("evidence") if isinstance(data.get("evidence"), dict) else {}
    for key in keys:
        if data.get(key) not in (None, ""):
            return data[key]
        if evidence.get(key) not in (None, ""):
            return evidence[key]
    return None


def _summary(escalation: str, dimensions: list[str], candidate: dict[str, Any]) -> str:
    anomaly_id = _value(candidate, "event_id", "anomaly_id", "id") or "历史异常"
    if escalation == "dealer_pattern":
        return f"{anomaly_id} 与当前异常共享经销商维度，且涉及不同代表，建议提升为经销商模式异常。"
    if escalation == "regional_pattern":
        return f"{anomaly_id} 与当前异常存在区域共性，建议纳入区域批量复核。"
    return f"{anomaly_id} 与当前异常在 {', '.join(dimensions)} 维度相似，建议合并复盘。"


def _as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {}
