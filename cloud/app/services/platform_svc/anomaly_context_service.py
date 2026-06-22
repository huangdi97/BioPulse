"""异常帮解释服务 — 主动收集能解释异常的数据。"""

from dataclasses import dataclass


@dataclass
class EvidenceItem:
    source: str
    finding: str


@dataclass
class AnomalyContext:
    anomaly: dict
    auto_evidence: list[dict]
    suggested_narrative: str


_SAMPLE_EVIDENCE: dict[str, list[dict]] = {
    "visit_inflation": [
        {"source": "GPS", "finding": "拜访轨迹集中在目标医院，非全城散点"},
        {"source": "商机", "finding": "pipeline中有一个大单在推进"},
        {"source": "竞品", "finding": "竞品同期在该区域有学术活动"},
        {"source": "费用", "finding": "差旅费用与拜访量等比增长，无异常"},
    ],
    "expense_anomaly": [
        {"source": "费用", "finding": "差旅费用上涨集中在周三固定会议"},
        {"source": "GPS", "finding": "轨迹与费用记录一致，无绕路"},
        {"source": "拜访", "finding": "拜访量同比+15%，符合费用增长趋势"},
    ],
    "compliance_risk": [
        {"source": "合规", "finding": "该代表历史合规记录良好，无违规"},
        {"source": "培训", "finding": "本月已完成合规培训并通过考核"},
        {"source": "商机", "finding": "当前商机阶段有特殊合规要求"},
    ],
}


class AnomalyContextService:
    async def gather_context(self, anomaly_id: str, rep_id: str) -> AnomalyContext:
        anomaly_info = self._resolve_anomaly(anomaly_id, rep_id)
        evidence = self._collect_evidence(anomaly_info["type"])
        narrative = self._build_narrative(anomaly_info, evidence)
        return AnomalyContext(
            anomaly=anomaly_info,
            auto_evidence=evidence,
            suggested_narrative=narrative,
        )

    def _resolve_anomaly(self, anomaly_id: str, rep_id: str) -> dict:
        types = {
            "a1": {"type": "拜访虚高", "detail": "本月拜访量+40%，流向仅+5%"},
            "a2": {"type": "费用异常", "detail": "差旅费用环比+30%，无对应流向增长"},
            "a3": {"type": "合规风险", "detail": "某HCP拜访频率超过季度上限"},
        }
        return types.get(anomaly_id, {"type": "未知异常", "detail": f"异常ID: {anomaly_id}"})

    def _collect_evidence(self, anomaly_type: str) -> list[dict]:
        return _SAMPLE_EVIDENCE.get(
            {"拜访虚高": "visit_inflation", "费用异常": "expense_anomaly", "合规风险": "compliance_risk"}.get(anomaly_type, ""),
            [{"source": "系统", "finding": "该异常类型暂无自动收集的证据"}],
        )

    def _build_narrative(self, anomaly: dict, evidence: list[dict]) -> str:
        sources = [e["source"] for e in evidence]
        return f"该代表的{'和'.join(sources)}数据可解释{anomaly['type']}。系统已自动收集相关证据，建议代表补充说明后提交。"
