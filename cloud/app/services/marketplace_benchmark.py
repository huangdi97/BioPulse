"""智能体市场基准测试方法。"""

import json
import statistics
from datetime import datetime
from typing import Optional
from uuid import uuid4

from cloud.app.repositories import BenchmarkReportsRepository, EffectMetricsRepository


class MarketplaceBenchmarkMixin:
    """效果度量百分位和基准测试报告方法。"""

    def _compute_percentiles(self, values: list) -> dict:
        """计算数值列表的百分位数分布。

        Args:
            values: 数值列表

        Returns:
            含 p5/p25/p50/p75/p90/p95/p99 的字典
        """
        if not values:
            return {}
        sorted_vals = sorted(values)
        n = len(sorted_vals)

        def _percentile(p):
            """按线性插值计算单个百分位值。"""
            k = (p / 100.0) * (n - 1)
            f = int(k)
            c = k - f
            if f + 1 < n:
                return round(sorted_vals[f] + c * (sorted_vals[f + 1] - sorted_vals[f]), 4)
            return round(sorted_vals[f], 4)

        return {
            "p5": _percentile(5),
            "p25": _percentile(25),
            "p50": _percentile(50),
            "p75": _percentile(75),
            "p90": _percentile(90),
            "p95": _percentile(95),
            "p99": _percentile(99),
        }

    def _compute_agent_percentile_rank(self, agent_value: float, all_values: list) -> float:
        """计算 Agent 指标值在全部值中的百分位排名。

        Args:
            agent_value: Agent 的指标值
            all_values: 全部 Agent 的指标值列表

        Returns:
            百分位排名（0-100）
        """
        if not all_values:
            return 0.0
        below = sum(1 for v in all_values if v <= agent_value)
        return round(below / len(all_values) * 100, 2)

    def generate_benchmark(self, report_name: str, report_type: str = "", period: str = "") -> dict:
        """生成基准测试报告。

        Args:
            report_name: 报告名称
            report_type: 报告类型（efficiency/quality/cost/general）
            period: 时间周期（start/end）

        Returns:
            含 industry_comparison 和 agent_rankings 的基准报告
        """
        bench_repo = BenchmarkReportsRepository(self.db)
        metrics_repo = EffectMetricsRepository(self.db)

        period_start = None
        period_end = None
        if period:
            parts = period.split("/")
            if len(parts) == 2:
                period_start, period_end = parts[0], parts[1]

        all_metrics = metrics_repo.list_all_metrics(period_start=period_start, period_end=period_end)

        industry_by_type = {}
        for m in all_metrics:
            mt = m["metric_type"]
            if mt not in industry_by_type:
                industry_by_type[mt] = []
            industry_by_type[mt].append(m["metric_value"])

        industry_comparison = {}
        for mt, vals in industry_by_type.items():
            if not vals:
                continue
            industry_comparison[mt] = {
                "count": len(vals),
                "min": round(min(vals), 4),
                "max": round(max(vals), 4),
                "mean": round(statistics.mean(vals), 4),
                "median": round(statistics.median(vals), 4),
                "stddev": round(statistics.stdev(vals), 4) if len(vals) > 1 else 0.0,
                "percentiles": self._compute_percentiles(vals),
            }

        agent_rankings = {}
        for m in all_metrics:
            agent = m["agent_role"]
            mt = m["metric_type"]
            all_vals = industry_by_type.get(mt, [])
            rank = self._compute_agent_percentile_rank(m["metric_value"], all_vals)
            if agent not in agent_rankings:
                agent_rankings[agent] = {}
            agent_rankings[agent][mt] = {
                "value": m["metric_value"],
                "unit": m.get("metric_unit", ""),
                "percentile": rank,
            }

        metrics_payload = {
            "industry_comparison": industry_comparison,
            "agent_rankings": agent_rankings,
        }

        report_id = f"bm:{uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        report_type_labels = {
            "efficiency": "效率",
            "quality": "质量",
            "cost": "成本",
            "general": "综合",
        }
        label = report_type_labels.get(report_type, "综合") if report_type else "综合"
        summary = f"{report_name}{label}基准报告（{len(agent_rankings)} 类智能体，{len(industry_comparison)} 项指标）"

        bench_repo.create(
            {
                "report_id": report_id,
                "report_name": report_name,
                "report_type": report_type or None,
                "summary": summary,
                "metrics": json.dumps(metrics_payload, ensure_ascii=False),
                "period": period or None,
                "created_at": now,
            }
        )
        return {
            "report_id": report_id,
            "industry_comparison": industry_comparison,
            "agent_rankings": agent_rankings,
        }

    def list_benchmarks(self, report_type: Optional[str] = None) -> list:
        """列出基准测试报告。

        Args:
            report_type: 按报告类型筛选

        Returns:
            基准报告列表
        """
        bench_repo = BenchmarkReportsRepository(self.db)
        rows = bench_repo.list_by_report_type(report_type=report_type)
        result = []
        for r in rows:
            result.append(
                {
                    "report_id": r["report_id"],
                    "report_name": r["report_name"],
                    "report_type": r["report_type"],
                    "data_source": r.get("data_source"),
                    "summary": r["summary"],
                    "metrics": json.loads(r["metrics"]) if r.get("metrics") else {},
                    "period": r.get("period"),
                    "created_at": r["created_at"],
                }
            )
        return result
