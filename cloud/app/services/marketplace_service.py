"""智能体市场服务，负责效果度量与基准测试管理。"""

import json
import statistics
from datetime import datetime
from typing import Optional
from uuid import uuid4

from cloud.app.repositories import (
    AgentMarketplaceRepository,
    BenchmarkReportsRepository,
    EffectMetricsRepository,
)
from cloud.app.services.base import BaseService


class MarketplaceService(BaseService):
    """智能体市场服务，提供效果度量上报、基准测试与仪表盘统计。"""

    def log_metric(
        self,
        agent_role: str,
        metric_type: str,
        metric_value: float,
        metric_unit: str = "",
        period_start: str = "",
        period_end: str = "",
    ) -> dict:
        metrics_repo = EffectMetricsRepository(self.db)
        metric_id = f"em:{uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        metrics_repo.create(
            {
                "metric_id": metric_id,
                "agent_role": agent_role,
                "metric_type": metric_type,
                "metric_value": metric_value,
                "metric_unit": metric_unit,
                "period_start": period_start or None,
                "period_end": period_end or None,
                "created_at": now,
            }
        )
        return {"metric_id": metric_id}

    def metrics_dashboard(self, agent_role: Optional[str] = None) -> list:
        metrics_repo = EffectMetricsRepository(self.db)
        rows = metrics_repo.dashboard(agent_role=agent_role)
        result = []
        for r in rows:
            result.append(
                {
                    "agent_role": r["agent_role"],
                    "metric_type": r["metric_type"],
                    "total": r["total"],
                    "avg_value": round(r["avg_value"], 4) if r["avg_value"] is not None else None,
                }
            )
        return result

    def _compute_percentiles(self, values: list) -> dict:
        if not values:
            return {}
        sorted_vals = sorted(values)
        n = len(sorted_vals)

        def _percentile(p):
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
        if not all_values:
            return 0.0
        below = sum(1 for v in all_values if v <= agent_value)
        return round(below / len(all_values) * 100, 2)

    def generate_benchmark(self, report_name: str, report_type: str = "", period: str = "") -> dict:
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

    def publish_item(
        self,
        item_name: str,
        description: str,
        agent_config: dict,
        category: str,
        price_model: str,
        publisher_sub: str,
    ) -> dict:
        marketplace_repo = AgentMarketplaceRepository(self.db)
        item_id = f"mp:{uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        marketplace_repo.create(
            {
                "item_id": item_id,
                "item_name": item_name,
                "item_type": "template",
                "description": description or None,
                "agent_config": json.dumps(agent_config, ensure_ascii=False),
                "category": category or None,
                "price_model": price_model,
                "rating": 0.0,
                "download_count": 0,
                "enabled": 1,
                "publisher": str(publisher_sub),
                "created_at": now,
            }
        )
        return {"item_id": item_id}

    def discover_items(
        self,
        category: Optional[str] = None,
        price_model: Optional[str] = None,
        enabled: Optional[int] = None,
    ) -> list:
        marketplace_repo = AgentMarketplaceRepository(self.db)
        rows = marketplace_repo.list_filtered(category=category, price_model=price_model, enabled=enabled)
        result = []
        for r in rows:
            result.append(
                {
                    "item_id": r.get("item_id"),
                    "item_name": r.get("item_name"),
                    "item_type": r.get("item_type"),
                    "description": r.get("description"),
                    "agent_config": json.loads(r["agent_config"]) if r.get("agent_config") else {},
                    "category": r.get("category"),
                    "price_model": r.get("price_model"),
                    "rating": r.get("rating"),
                    "download_count": r.get("download_count"),
                    "enabled": bool(r.get("enabled")),
                    "publisher": r.get("publisher"),
                    "created_at": r.get("created_at"),
                }
            )
        return result
