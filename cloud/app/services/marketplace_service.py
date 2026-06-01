import json
from datetime import datetime
from typing import Optional
from uuid import uuid4

from cloud.app.repositories import EffectMetricsRepository, BenchmarkReportsRepository, AgentMarketplaceRepository
from cloud.app.services.base import BaseService


class MarketplaceService(BaseService):
    def log_metric(self, agent_role: str, metric_type: str, metric_value: float,
                   metric_unit: str = "", period_start: str = "",
                   period_end: str = "") -> dict:
        metrics_repo = EffectMetricsRepository(self.db)
        metric_id = f"em:{uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        metrics_repo.create({
            "metric_id": metric_id,
            "agent_role": agent_role,
            "metric_type": metric_type,
            "metric_value": metric_value,
            "metric_unit": metric_unit,
            "period_start": period_start or None,
            "period_end": period_end or None,
            "created_at": now,
        })
        return {"metric_id": metric_id}

    def metrics_dashboard(self, agent_role: Optional[str] = None) -> list:
        metrics_repo = EffectMetricsRepository(self.db)
        rows = metrics_repo.dashboard(agent_role=agent_role)
        result = []
        for r in rows:
            result.append({
                "agent_role": r["agent_role"],
                "metric_type": r["metric_type"],
                "total": r["total"],
                "avg_value": round(r["avg_value"], 4) if r["avg_value"] is not None else None,
            })
        return result

    def generate_benchmark(self, report_name: str, report_type: str = "",
                           period: str = "") -> dict:
        bench_repo = BenchmarkReportsRepository(self.db)
        report_id = f"bm:{uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        bench_repo.create({
            "report_id": report_id,
            "report_name": report_name,
            "report_type": report_type or None,
            "summary": f"{report_name}报告",
            "metrics": json.dumps({}, ensure_ascii=False),
            "period": period or None,
            "created_at": now,
        })
        return {"report_id": report_id}

    def list_benchmarks(self, report_type: Optional[str] = None) -> list:
        bench_repo = BenchmarkReportsRepository(self.db)
        rows = bench_repo.list_by_report_type(report_type=report_type)
        result = []
        for r in rows:
            result.append({
                "report_id": r["report_id"],
                "report_name": r["report_name"],
                "report_type": r["report_type"],
                "data_source": r.get("data_source"),
                "summary": r["summary"],
                "metrics": json.loads(r["metrics"]) if r.get("metrics") else {},
                "period": r.get("period"),
                "created_at": r["created_at"],
            })
        return result

    def publish_item(self, item_name: str, description: str, agent_config: dict,
                     category: str, price_model: str, publisher_sub: str) -> dict:
        marketplace_repo = AgentMarketplaceRepository(self.db)
        item_id = f"mp:{uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        marketplace_repo.create({
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
        })
        return {"item_id": item_id}

    def discover_items(self, category: Optional[str] = None,
                       price_model: Optional[str] = None,
                       enabled: Optional[int] = None) -> list:
        marketplace_repo = AgentMarketplaceRepository(self.db)
        rows = marketplace_repo.list_filtered(
            category=category, price_model=price_model, enabled=enabled)
        result = []
        for r in rows:
            result.append({
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
            })
        return result
