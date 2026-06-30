"""假设推演引擎——基于历史基线 + 因果推断对干预方案做多维影响推演与方案对比。"""

from cloud.app.services.brain.causal_service import CausalService

_METRICS = ("flow_change", "compliance_risk_change", "cost_change")

_HISTORICAL_BASELINES = {
    "华南": {"flow": 0.0500, "compliance_risk": 0.0200, "cost": -0.0100},
    "华东": {"flow": 0.0300, "compliance_risk": 0.0100, "cost": 0.0000},
    "华北": {"flow": -0.0200, "compliance_risk": 0.0300, "cost": 0.0200},
}
_DEFAULT_BASELINE = {"flow": 0.0, "compliance_risk": 0.01, "cost": 0.01}

_ELASTICITY = {
    "visit_freq_change": {"flow": 1.8, "compliance_risk": -0.3, "cost": 0.9},
    "discount_depth_change": {"flow": 2.2, "compliance_risk": 0.6, "cost": -1.5},
    "coverage_change": {"flow": 1.2, "compliance_risk": -0.1, "cost": 0.6},
    "academic_activity_change": {"flow": 0.9, "compliance_risk": -0.2, "cost": 1.1},
}

_DIRECTION_THRESHOLD = 0.005
_CONFIDENCE_SPREAD_RATIO = 0.15
_CONFIDENCE_FLOOR = 0.005


def _get_baseline(intervention: dict) -> dict:
    return _HISTORICAL_BASELINES.get(intervention.get("region", ""), _DEFAULT_BASELINE)


def _compute_metric(metric: str, intervention: dict, weights: dict) -> float:
    base_key = metric.split("_")[0]
    base_val = _get_baseline(intervention).get(base_key, 0.0)
    total_effect = 0.0
    for var_name, change in intervention.items():
        if var_name in ("region", "scenario_name"):
            continue
        elas = _ELASTICITY.get(var_name, {})
        total_effect += change * elas.get(metric, 0.0)
    return base_val + total_effect * weights.get(metric, 1.0)


def _direction(val: float) -> str:
    if val > _DIRECTION_THRESHOLD:
        return "up"
    if val < -_DIRECTION_THRESHOLD:
        return "down"
    return "stable"


def _confidence_interval(val: float) -> list[float]:
    spread = max(abs(val * _CONFIDENCE_SPREAD_RATIO), _CONFIDENCE_FLOOR)
    return [round(val - spread, 4), round(val + spread, 4)]


class WhatIfEngine:
    """假设推演引擎，对干预方案做多维影响推演与方案对比。

    基于区域历史基线 + 弹性系数 + 因果权重，预测流向、合规风险、费用
    三个维度的变化量，并给出置信区间与变动方向。
    """

    def __init__(self, causal_service: CausalService | None = None):
        self._causal = causal_service or CausalService()

    def simulate(self, intervention: dict) -> dict:
        """对单条干预方案执行多维影响推演。

        Args:
            intervention: 干预变量字典。
                支持键包括 region / scenario_name 以及连续变量如
                visit_freq_change（拜访频率变化量，如 0.20）、
                discount_depth_change / coverage_change 等。

        Returns:
            每个指标含 predicted_value、confidence_interval、direction。
        """
        return self._run(intervention)

    def compare_scenarios(self, scenarios: list[dict]) -> dict:
        """对比多个干预方案并返回汇总结果。

        Args:
            scenarios: 方案列表，每项为含 scenario_name 的干预字典。

        Returns:
            {scenario_name: {metric: {predicted_value, confidence_interval, direction}}}
        """
        return {s.get("scenario_name", f"scenario_{i}"): self._run(s) for i, s in enumerate(scenarios)}

    def _run(self, intervention: dict) -> dict:
        features = {k: v for k, v in intervention.items() if k not in ("region", "scenario_name")}
        causal_result = self._causal.causal_infer(features=features, target="overall_impact")
        weights = causal_result.get("feature_weights", {})

        out = {}
        for metric in _METRICS:
            val = _compute_metric(metric, intervention, weights)
            out[metric] = {
                "predicted_value": round(val, 4),
                "confidence_interval": _confidence_interval(val),
                "direction": _direction(val),
            }
        return out
