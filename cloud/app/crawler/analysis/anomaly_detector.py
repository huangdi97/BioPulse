"""Statistical price anomaly detection."""

from __future__ import annotations

import math
from typing import Any

from cloud.app.crawler.analysis import load_price_records, safe_float


class AnomalyDetector:
    """Detect price outliers using the 3-sigma rule."""

    def __init__(self, storage: Any | None = None) -> None:
        self.storage = storage

    def detect_anomaly(self, product_id: int | str) -> dict[str, Any]:
        """Detect 3-sigma price anomalies over a 60-day window.

        Args:
            product_id: Product identifier.

        Returns:
            Dict with sample_count, has_anomaly flag, mean, std_dev, bounds, and anomaly list.
        """
        records = load_price_records(product_id, days=60, storage=self.storage)
        prices = [safe_float(record.get("price")) for record in records]
        if not prices:
            return {
                "product_id": int(product_id),
                "sample_count": 0,
                "has_anomaly": False,
                "anomalies": [],
                "mean": 0.0,
                "std_dev": 0.0,
            }

        n = len(prices)
        mean = sum(prices) / n
        variance = sum((price - mean) ** 2 for price in prices) / (n - 1) if n > 1 else 0.0
        std_dev = math.sqrt(variance)
        anomalies = []
        for record in records:
            price = safe_float(record.get("price"))
            z_score = (price - mean) / std_dev if std_dev else 0.0
            if abs(z_score) >= 3:
                anomalies.append(
                    {
                        "date": record["date"],
                        "province": record.get("province") or "全国",
                        "price": round(price, 2),
                        "z_score": round(z_score, 2),
                        "direction": "high" if z_score > 0 else "low",
                    }
                )

        return {
            "product_id": int(product_id),
            "sample_count": len(records),
            "has_anomaly": bool(anomalies),
            "anomalies": anomalies,
            "mean": round(mean, 2),
            "std_dev": round(std_dev, 2),
            "upper_bound": round(mean + 3 * std_dev, 2),
            "lower_bound": round(mean - 3 * std_dev, 2),
        }


def detect_anomaly(product_id: int | str) -> dict[str, Any]:
    """Convenience function: run anomaly detection with a default detector."""
    return AnomalyDetector().detect_anomaly(product_id)


__all__ = ["AnomalyDetector", "detect_anomaly"]
