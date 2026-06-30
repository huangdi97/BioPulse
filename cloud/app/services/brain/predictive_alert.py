"""预测性告警服务 — 基于时序数据的线性回归趋势预测与分级告警"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from shared.base_service import BaseService

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    metric_name: str
    level: str
    predicted_value: float
    threshold: float
    days_to_breach: int
    created_at: datetime = field(default_factory=datetime.now)


class PredictiveAlertService(BaseService):
    """基于线性回归的趋势预测与分级告警。"""

    def __init__(self, db=None):
        super().__init__(db)
        self._active_alerts: dict[str, list[Alert]] = {}

    @staticmethod
    def _linear_regression(values: list[float]) -> tuple[float, float, float]:
        n = len(values)
        if n < 2:
            return 0.0, values[-1] if values else 0.0, 0.0
        xs = list(range(n))
        sx = sum(xs)
        sy = sum(values)
        sxy = sum(x * y for x, y in zip(xs, values))
        sxx = sum(x * x for x in xs)
        denom = n * sxx - sx * sx
        if denom == 0:
            return 0.0, sy / n, 0.0
        slope = (n * sxy - sx * sy) / denom
        intercept = (sy - slope * sx) / n
        y_hat = [slope * x + intercept for x in xs]
        ss_res = sum((y - yh) ** 2 for y, yh in zip(values, y_hat))
        ss_tot = sum((y - sy / n) ** 2 for y in values)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        return slope, intercept, r2

    def predict_trend(self, metric_name: str, historical_data: list[dict[str, Any]]) -> dict[str, Any]:
        """基于历史时序数据用简单线性回归预测未来 7/14/28 天趋势。"""
        values = [p["value"] for p in historical_data]
        slope, intercept, r2 = self._linear_regression(values)
        latest_value = values[-1] if values else 0.0
        predictions: dict[str, float] = {}
        last_x = len(values) - 1
        for days in (7, 14, 28):
            predictions[f"day_{days}"] = round(slope * (last_x + days) + intercept, 4)
        return {
            "metric_name": metric_name,
            "latest_value": latest_value,
            "predictions": predictions,
            "slope": round(slope, 4),
            "r_squared": round(r2, 4),
            "trend": "up" if slope > 0 else ("down" if slope < 0 else "stable"),
        }

    def check_alerts(self, tenant_id: str) -> list[Alert]:
        """预测值低于阈值时触发分级告警 (🟡4周后/🟠2周后/🔴1周内)。"""
        conn = self._connection()
        thresholds = self._load_thresholds(conn, tenant_id)
        if not thresholds:
            logger.info("No thresholds for tenant %s", tenant_id)
            return []

        triggered: list[Alert] = []
        for metric_name, threshold in thresholds.items():
            data = conn.execute(
                "SELECT value, recorded_at FROM metric_records WHERE tenant_id=? AND metric_name=? ORDER BY recorded_at ASC",
                (tenant_id, metric_name),
            ).fetchall()
            if len(data) < 2:
                continue
            historical = [{"value": r["value"]} for r in data]
            trend = self.predict_trend(metric_name, historical)
            if trend["trend"] != "down":
                continue
            pred = trend["predictions"]
            for days, label in [(28, "🟡 info"), (14, "🟠 warning"), (7, "🔴 critical")]:
                if pred.get(f"day_{days}", threshold) < threshold:
                    triggered.append(
                        Alert(
                            metric_name=metric_name,
                            level=label,
                            predicted_value=pred[f"day_{days}"],
                            threshold=threshold,
                            days_to_breach=days,
                        )
                    )
                    break

        if triggered:
            self._active_alerts.setdefault(tenant_id, []).extend(triggered)
        return triggered

    def get_active_alerts(self, tenant_id: str) -> list[Alert]:
        """返回当前活跃的告警列表。"""
        return self._active_alerts.get(tenant_id, [])

    def _load_thresholds(self, conn: Any, tenant_id: str) -> dict[str, float]:
        rows = conn.execute(
            "SELECT metric_name, threshold_value FROM alert_thresholds WHERE tenant_id=?",
            (tenant_id,),
        ).fetchall()
        return {r["metric_name"]: r["threshold_value"] for r in rows} or {}
