"""Cross-province and cross-competitor price comparison."""

from __future__ import annotations

from typing import Any

from cloud.app.crawler.analysis import latest_by, load_price_records, pct_change, safe_float


class ComparisonAnalyzer:
    """Compare latest prices between provinces or competitor products."""

    def __init__(self, storage: Any | None = None) -> None:
        self.storage = storage

    def compare_provinces(self, product_id: int | str) -> dict[str, Any]:
        """Compare latest price across provinces for a single product.

        Args:
            product_id: Product identifier.

        Returns:
            Dict with province_count, average_price, lowest/highest details, spread, and province list.
        """
        records = load_price_records(product_id, days=30, storage=self.storage)
        latest = latest_by(records, "province")
        province_prices = [
            {
                "province": province or "全国",
                "price": round(safe_float(record.get("price")), 2),
                "date": record["date"],
            }
            for province, record in latest.items()
        ]
        province_prices.sort(key=lambda item: item["price"])
        prices = [item["price"] for item in province_prices]
        lowest = province_prices[0] if province_prices else None
        highest = province_prices[-1] if province_prices else None
        average = round(sum(prices) / len(prices), 2) if prices else 0.0

        return {
            "product_id": int(product_id),
            "province_count": len(province_prices),
            "average_price": average,
            "lowest": lowest,
            "highest": highest,
            "spread": round((highest["price"] - lowest["price"]), 2) if lowest and highest else 0.0,
            "spread_pct": pct_change(lowest["price"], highest["price"]) if lowest and highest else 0.0,
            "provinces": province_prices,
        }

    def compare_competitors(self, product_ids: list[int | str]) -> dict[str, Any]:
        """Compare latest prices across multiple competitor products.

        Args:
            product_ids: List of product identifiers.

        Returns:
            Dict with product_count, lowest/highest product details, and ranked competitor list.
        """
        competitors = []
        for product_id in product_ids:
            records = load_price_records(product_id, days=14, storage=self.storage)
            if not records:
                continue
            latest_date = max((record["date"] for record in records), default="")
            latest_records = [record for record in records if record["date"] == latest_date]
            latest_price = (
                round(sum(safe_float(record.get("price")) for record in latest_records) / len(latest_records), 2) if latest_records else 0.0
            )
            competitors.append(
                {
                    "product_id": int(product_id),
                    "latest_price": latest_price,
                    "latest_date": latest_date,
                    "province_count": len({record.get("province") for record in latest_records}),
                }
            )

        competitors.sort(key=lambda item: item["latest_price"])
        baseline = competitors[0]["latest_price"] if competitors else 0.0
        for rank, item in enumerate(competitors, start=1):
            item["rank"] = rank
            item["premium_vs_lowest_pct"] = pct_change(baseline, item["latest_price"]) if baseline else 0.0

        return {
            "product_count": len(competitors),
            "lowest_product": competitors[0] if competitors else None,
            "highest_product": competitors[-1] if competitors else None,
            "competitors": competitors,
        }


def compare_provinces(product_id: int | str) -> dict[str, Any]:
    """Convenience function: compare provinces with a default analyzer."""
    return ComparisonAnalyzer().compare_provinces(product_id)


def compare_competitors(product_ids: list[int | str]) -> dict[str, Any]:
    """Convenience function: compare competitors with a default analyzer."""
    return ComparisonAnalyzer().compare_competitors(product_ids)


__all__ = ["ComparisonAnalyzer", "compare_competitors", "compare_provinces"]
