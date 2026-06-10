"""Hypothesis generation for red-light and anomaly events."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Hypothesis:
    """A verifiable candidate explanation for one anomaly."""

    hypothesis_id: str
    anomaly_id: str
    description: str
    required_data: list[str]
    expected_signal: str
    root_cause_category: str
    prior_confidence: float = 0.5
    anomaly_event: dict[str, Any] = field(default_factory=dict)


class Hypothesizer:
    """Generate candidate root-cause hypotheses from anomaly evidence."""

    def generate_hypotheses(self, anomaly_event: Any) -> list[Hypothesis]:
        """Generate at least two verifiable hypotheses for an anomaly event.

        Args:
            anomaly_event: Red-light or anomaly event as a dict or dataclass-like object.

        Returns:
            Candidate hypotheses ordered by signal strength.
        """
        event = _as_dict(anomaly_event)
        evidence = _as_dict(event.get("evidence", {}))
        anomaly_id = _first_text(event, "event_id", "anomaly_id", "id") or "anomaly-unknown"
        signals = _flatten_text(event, evidence)
        candidates: list[Hypothesis] = []

        if _has_any(signals, ("expense", "费用", "reimburse", "invoice", "amount", "金额")) or _any_truthy(
            evidence,
            ("expense_without_visit", "expense_visit_mismatch", "amount_mismatch", "invoice_mismatch"),
        ):
            candidates.append(
                self._build(
                    event,
                    anomaly_id,
                    "expense_visit_mismatch",
                    "费用记录与拜访或流向证据不一致，可能存在费用真实性问题。",
                    ["expense_records", "visit_records", "distribution_trace", "invoice_records"],
                    "同一时间窗内费用、拜访、流向至少两类证据无法互相印证。",
                    0.72,
                )
            )

        if _first_text(event, "dealer_id", "dealer", "distributor_id", "distributor") or _first_text(
            evidence, "dealer_id", "dealer", "distributor_id", "distributor"
        ):
            candidates.append(
                self._build(
                    event,
                    anomaly_id,
                    "distributor_concentration",
                    "异常集中在同一经销商或配送链路，可能不是单个代表行为，而是渠道模式异常。",
                    ["dealer_orders", "distribution_trace", "rep_activity", "historical_anomalies"],
                    "同一经销商下多个代表、多个订单或多个时间段出现相似异常。",
                    0.68,
                )
            )

        if _has_any(signals, ("visit", "拜访", "route", "gps", "location", "签到", "time", "时间")) or _any_truthy(
            evidence,
            ("route_anomaly", "gps_anomaly", "visit_gap", "time_conflict", "location_mismatch"),
        ):
            candidates.append(
                self._build(
                    event,
                    anomaly_id,
                    "visit_execution_gap",
                    "拜访执行轨迹存在时间、地点或顺序异常，可能存在未真实完成拜访的问题。",
                    ["visit_records", "route_trace", "gps_checkins", "hcp_confirmation"],
                    "拜访签到、GPS、HCP确认或路线顺序之间出现冲突。",
                    0.64,
                )
            )

        if _has_any(signals, ("duplicate", "重复", "missing", "缺失", "sync", "同步", "data")) or _any_truthy(
            evidence,
            ("duplicate_record", "missing_data", "late_sync", "data_quality_issue"),
        ):
            candidates.append(
                self._build(
                    event,
                    anomaly_id,
                    "data_quality_issue",
                    "异常可能由重复上报、延迟同步或关键字段缺失导致。",
                    ["source_records", "sync_logs", "dedupe_keys", "operator_logs"],
                    "源系统存在重复主键、延迟入湖、字段缺失或人工修订记录。",
                    0.56,
                )
            )

        candidates.append(
            self._build(
                event,
                anomaly_id,
                "policy_rule_breach",
                "红灯由明确合规规则触发，可能是规则命中的直接违规行为。",
                ["rule_hit_detail", "audit_log", "policy_threshold", "supporting_evidence"],
                "规则命中详情与审计证据可以直接支撑红灯等级。",
                0.62,
            )
        )

        unique = _dedupe(candidates)
        if len(unique) == 1:
            unique.append(
                self._build(
                    event,
                    anomaly_id,
                    "data_quality_issue",
                    "异常也可能由数据质量或接口同步问题造成，需要排除误报。",
                    ["source_records", "sync_logs", "dedupe_keys"],
                    "源记录存在重复、缺失或延迟同步。",
                    0.45,
                )
            )
        return sorted(unique, key=lambda item: item.prior_confidence, reverse=True)

    def _build(
        self,
        event: dict[str, Any],
        anomaly_id: str,
        category: str,
        description: str,
        required_data: list[str],
        expected_signal: str,
        prior_confidence: float,
    ) -> Hypothesis:
        return Hypothesis(
            hypothesis_id=f"{anomaly_id}:{category}",
            anomaly_id=anomaly_id,
            description=description,
            required_data=required_data,
            expected_signal=expected_signal,
            root_cause_category=category,
            prior_confidence=prior_confidence,
            anomaly_event=event,
        )


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


def _first_text(data: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def _flatten_text(*items: dict[str, Any]) -> str:
    parts: list[str] = []
    for item in items:
        for value in item.values():
            if isinstance(value, (str, int, float, bool)):
                parts.append(str(value))
            elif isinstance(value, list):
                parts.extend(str(v) for v in value[:10])
            elif isinstance(value, dict):
                parts.extend(str(v) for v in value.values())
    return " ".join(parts).lower()


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle.lower() in text for needle in needles)


def _any_truthy(data: dict[str, Any], keys: tuple[str, ...]) -> bool:
    return any(bool(data.get(key)) for key in keys)


def _dedupe(candidates: list[Hypothesis]) -> list[Hypothesis]:
    seen: set[str] = set()
    unique: list[Hypothesis] = []
    for candidate in candidates:
        if candidate.root_cause_category in seen:
            continue
        seen.add(candidate.root_cause_category)
        unique.append(candidate)
    return unique
