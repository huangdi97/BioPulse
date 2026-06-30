"""多租户行业基准计算——从SharedState匿名聚合，防反推。"""

from typing import Optional

METRICS_LABELS = {
    "visit_frequency": "拜访频次",
    "cost_efficiency": "费用效率",
    "compliance_rate": "合规率",
    "hcp_coverage": "HCP覆盖率",
    "conversion_rate": "商机转化率",
}
MIN_TENANTS = 3


def _percentile(sorted_vals: list[float], p: float) -> float:
    n = len(sorted_vals)
    k = (p / 100.0) * (n - 1)
    f = int(k)
    c = k - f
    if f + 1 < n:
        return round(sorted_vals[f] + c * (sorted_vals[f + 1] - sorted_vals[f]), 4)
    return round(sorted_vals[f], 4)


class IndustryBenchmark:
    def __init__(self):
        self._ss = None

    @property
    def ss(self):
        if self._ss is None:
            from cloud.app.agent_runtime.core.shared_state import get_shared_state

            self._ss = get_shared_state()
        return self._ss

    def record_metric(self, tenant_id: str, metric: str, value: float) -> None:
        from cloud.app.agent_runtime.core.shared_state import SharedStateEntry

        entry = SharedStateEntry(
            namespace="industry_benchmark",
            key=f"{metric}.{tenant_id}",
            value={"tenant_id": tenant_id, "metric": metric, "value": value},
            agent_key="industry_benchmark",
            confidence=1.0,
            evidence=[f"tenant.{tenant_id}.{metric}"],
        )
        self.ss.write(entry, caller_agent_key="industry_benchmark")

    def _collect_all(self) -> dict[str, dict[str, float]]:
        namespaces = self.ss.list_all_namespaces()
        tenant_metrics: dict[str, dict[str, float]] = {}
        for full_ns, entries in namespaces.items():
            parts = full_ns.split(".")
            if len(parts) < 2 or parts[-1] != "industry_benchmark":
                continue
            tenant_id = parts[0]
            metrics: dict[str, float] = {}
            for e in entries:
                if isinstance(e, dict):
                    m = e.get("metric")
                    v = e.get("value")
                    if m and v is not None:
                        metrics[m] = float(v)
            if metrics:
                tenant_metrics[tenant_id] = metrics
        return tenant_metrics

    def compute_benchmarks(self) -> dict[str, dict[str, float]]:
        tenant_metrics = self._collect_all()
        if len(tenant_metrics) < MIN_TENANTS:
            return {}
        metric_pool: dict[str, list[float]] = {}
        for tm in tenant_metrics.values():
            for m, v in tm.items():
                metric_pool.setdefault(m, []).append(v)
        result: dict[str, dict[str, float]] = {}
        for m, vals in metric_pool.items():
            sv = sorted(vals)
            result[m] = {
                "p25": _percentile(sv, 25),
                "p50": _percentile(sv, 50),
                "p75": _percentile(sv, 75),
            }
        return result

    def get_percentile_rank(self, tenant_id: str, metric: str) -> dict:
        tenant_metrics = self._collect_all()
        if len(tenant_metrics) < MIN_TENANTS:
            return {}
        all_vals = []
        tenant_value: Optional[float] = None
        for tid, tm in tenant_metrics.items():
            v = tm.get(metric)
            if v is not None:
                all_vals.append(v)
                if tid == tenant_id:
                    tenant_value = v
        if tenant_value is None or len(all_vals) < MIN_TENANTS:
            return {}
        sv = sorted(all_vals)
        below = sum(1 for x in all_vals if x <= tenant_value)
        percentile_rank = round(below / len(all_vals) * 100, 2)
        return {
            metric: {
                "p25": _percentile(sv, 25),
                "p50": _percentile(sv, 50),
                "p75": _percentile(sv, 75),
                "tenant_value": tenant_value,
                "percentile_rank": percentile_rank,
            }
        }
