"""Threshold based price alerting."""

from __future__ import annotations

from typing import Any

from cloud.app.crawler.analysis import daily_average, load_price_records, pct_change


class ThresholdAlerter:
    """Trigger alerts when latest price movement crosses a percentage threshold."""

    def __init__(self, storage: Any | None = None, db: Any | None = None) -> None:
        self.storage = storage
        self.db = db

    def check_threshold(self, product_id: int | str, threshold_pct: float = 5.0, days: int = 14) -> dict[str, Any]:
        """Check if the latest daily-average price change exceeds the threshold.

        Args:
            product_id: Product identifier.
            threshold_pct: Percentage threshold for triggering (default 5%).
            days: Number of days of price history to load (default 14).

        Returns:
            Dict with triggered flag, price change details, direction, and optional notification.
        """
        records = load_price_records(product_id, days=days, storage=self.storage)
        series = daily_average(records)
        if len(series) < 2:
            return {
                "product_id": int(product_id),
                "triggered": False,
                "reason": "insufficient_price_history",
                "threshold_pct": threshold_pct,
            }

        previous = series[-2]["price"]
        latest = series[-1]["price"]
        change = pct_change(previous, latest)
        triggered = abs(change) >= threshold_pct
        alert = {
            "product_id": int(product_id),
            "triggered": triggered,
            "threshold_pct": threshold_pct,
            "previous_price": previous,
            "latest_price": latest,
            "change_pct": change,
            "direction": "increase" if change > 0 else "decrease" if change < 0 else "flat",
            "checked_date": series[-1]["date"],
        }
        if triggered:
            alert["notification"] = self._notify(alert)
        return alert

    def _notify(self, alert: dict[str, Any]) -> dict[str, Any]:
        # Send or simulate a price-threshold notification via the notification client.
        title = f"竞品价格阈值预警：产品{alert['product_id']}"
        body = f"最新价格变动 {alert['change_pct']}%，已达到阈值 {alert['threshold_pct']}%。"
        if self.db is None:
            return {"status": "simulated", "title": title, "body": body}
        try:
            from shared.notification_client import send_notification

            notification_id = send_notification(
                self.db,
                user_id=1,
                title=title,
                body=body,
                category="competitor_price_alert",
                ref_type="competitor_product",
                ref_id=alert["product_id"],
                context=alert,
            )
            return {"status": "sent", "notification_id": notification_id}
        except Exception as exc:
            return {"status": "failed", "error": str(exc)}


def check_threshold(product_id: int | str, threshold_pct: float = 5.0, days: int = 14) -> dict[str, Any]:
    """Convenience function: run threshold check with a default alerter."""
    return ThresholdAlerter().check_threshold(product_id, threshold_pct, days=days)


__all__ = ["ThresholdAlerter", "check_threshold"]
