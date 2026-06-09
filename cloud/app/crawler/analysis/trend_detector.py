"""Price trend detection for competitor products."""

from __future__ import annotations

from typing import Any

from cloud.app.crawler.analysis import daily_average, linear_regression_slope, load_price_records, moving_average, pct_change

# Threshold for slope percentage per day below which a trend is considered
# stable (0.08 means less than 0.08% daily price drift).
STABLE_SLOPE_PCT_PER_DAY = 0.08
# Minimum absolute percentage change over the window to override a stable
# classification; a change below 1% is considered noise.
STABLE_CHANGE_PCT_THRESHOLD = 1


class TrendDetector:
    """Detect price trends with moving averages and linear-regression slope."""

    def __init__(self, storage: Any | None = None) -> None:
        self.storage = storage

    def detect_trend(self, product_id: int | str, days: int = 30) -> dict[str, Any]:
        """Detect the price trend (rising/falling/stable) over the given window.

        Args:
            product_id: Product identifier.
            days: Number of days to analyze.

        Returns:
            Dict with trend label, price change, slope, and time series with moving averages.
        """
        records = load_price_records(product_id, days=days, storage=self.storage)
        series = daily_average(records)
        prices = [point["price"] for point in series]
        averages = moving_average(prices, window=7)
        slope = linear_regression_slope(averages or prices)
        first_price = prices[0] if prices else 0.0
        latest_price = prices[-1] if prices else 0.0
        change_pct = pct_change(first_price, latest_price)
        slope_pct_per_day = round((slope / first_price * 100), 4) if first_price else 0.0

        if abs(slope_pct_per_day) < STABLE_SLOPE_PCT_PER_DAY and abs(change_pct) < STABLE_CHANGE_PCT_THRESHOLD:
            trend = "stable"
        elif slope > 0:
            trend = "rising"
        else:
            trend = "falling"

        return {
            "product_id": int(product_id),
            "days": days,
            "sample_count": len(records),
            "trend": trend,
            "first_price": round(first_price, 2),
            "latest_price": round(latest_price, 2),
            "change_pct": change_pct,
            "linear_regression_slope": round(slope, 4),
            "slope_pct_per_day": slope_pct_per_day,
            "moving_average_window": min(7, len(prices)) if prices else 0,
            "series": [
                {
                    "date": point["date"],
                    "price": point["price"],
                    "moving_average": averages[idx] if idx < len(averages) else point["price"],
                }
                for idx, point in enumerate(series)
            ],
        }


def detect_trend(product_id: int | str, days: int = 30) -> dict[str, Any]:
    """Convenience function: run trend detection with a default detector."""
    return TrendDetector().detect_trend(product_id, days)


__all__ = ["TrendDetector", "detect_trend"]
