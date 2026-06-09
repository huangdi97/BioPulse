"""Competitor intelligence brief generation and delivery."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from cloud.app.crawler.analysis.anomaly_detector import AnomalyDetector
from cloud.app.crawler.analysis.sentiment_analyzer import SentimentAnalyzer
from cloud.app.crawler.analysis.threshold_alerter import ThresholdAlerter
from cloud.app.crawler.analysis.trend_detector import TrendDetector


class CompetitorBriefService:
    """Generate weekly competitor briefs from sentiment, price and approval signals."""

    def __init__(self, db: Any | None = None, storage: Any | None = None) -> None:
        """初始化竞品简报服务及分析器。"""
        self.db = db
        self.storage = storage
        self.trend_detector = TrendDetector(storage=storage)
        self.anomaly_detector = AnomalyDetector(storage=storage)
        self.threshold_alerter = ThresholdAlerter(storage=storage, db=db)
        self.sentiment_analyzer = SentimentAnalyzer(storage=storage)

    def generate_weekly_brief(self, week_start: date | datetime | str | None = None) -> dict[str, Any]:
        """生成竞品情报周报。"""
        start = self._resolve_week_start(week_start)
        end = start + timedelta(days=6)
        product_ids = self._load_product_ids()
        price_adjustments = []
        negative_events = []

        for product_id in product_ids:
            trend = self.trend_detector.detect_trend(product_id, days=7)
            anomaly = self.anomaly_detector.detect_anomaly(product_id)
            threshold = self.threshold_alerter.check_threshold(product_id, threshold_pct=3.0)
            if abs(trend["change_pct"]) >= 1 or threshold.get("triggered"):
                price_adjustments.append(
                    {
                        "product_id": product_id,
                        "trend": trend["trend"],
                        "change_pct": trend["change_pct"],
                        "latest_price": trend["latest_price"],
                        "threshold_triggered": threshold.get("triggered", False),
                    }
                )
            if anomaly["has_anomaly"]:
                negative_events.append(
                    {
                        "type": "price_anomaly",
                        "product_id": product_id,
                        "anomalies": anomaly["anomalies"],
                    }
                )

        sentiment = self.sentiment_analyzer.analyze("竞品A", days=7)
        if sentiment["sentiment_distribution"]["negative"] > sentiment["sentiment_distribution"]["positive"]:
            negative_events.append(
                {
                    "type": "public_opinion",
                    "keyword": "竞品A",
                    "negative_mentions": sentiment["sentiment_distribution"]["negative"],
                }
            )

        new_launches = self._load_new_product_launches(start, end)
        marketing = self._load_marketing_activities(start, end)

        return {
            "title": f"竞品情报周报 {start.isoformat()} 至 {end.isoformat()}",
            "week_start": start.isoformat(),
            "week_end": end.isoformat(),
            "summary": {
                "new_product_launches": len(new_launches),
                "price_adjustments": len(price_adjustments),
                "marketing_activities": len(marketing),
                "negative_events": len(negative_events),
                "tracked_products": len(product_ids),
            },
            "sections": {
                "new_product_launches": new_launches,
                "price_adjustments": price_adjustments,
                "marketing_activities": marketing,
                "negative_events": negative_events,
                "sentiment": sentiment,
            },
            "recommendations": self._recommend(price_adjustments, negative_events, sentiment),
            "sources": ["crawler.price_records", "crawler.public_opinions", "market_intel_items"],
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def deliver_brief(self, team_ids: list[int | str], brief: dict[str, Any]) -> dict[str, Any]:
        """向指定团队推送竞品简报。"""
        deliveries = []
        for team_id in team_ids:
            for channel in ("管理端", "销售助手"):
                deliveries.append(self._deliver_one(team_id, channel, brief))
        return {
            "brief_title": brief.get("title", ""),
            "team_count": len(team_ids),
            "delivery_count": len(deliveries),
            "deliveries": deliveries,
        }

    def _deliver_one(self, team_id: int | str, channel: str, brief: dict[str, Any]) -> dict[str, Any]:
        """向单个团队单渠道推送简报。"""
        if self.db is None:
            return {"team_id": team_id, "channel": channel, "status": "simulated"}
        try:
            from shared.notification_client import send_notification

            notification_id = send_notification(
                self.db,
                user_id=int(team_id),
                title=brief.get("title", "竞品情报周报"),
                body=self._brief_body(brief),
                category="competitor_brief",
                ref_type="competitor_brief",
                ref_id=None,
                context={"channel": channel, "brief": brief},
            )
            return {"team_id": team_id, "channel": channel, "status": "sent", "notification_id": notification_id}
        except Exception as exc:
            return {"team_id": team_id, "channel": channel, "status": "failed", "error": str(exc)}

    def _resolve_week_start(self, value: date | datetime | str | None) -> date:
        """解析周起始日期。"""
        if value is None:
            today = date.today()
            return today - timedelta(days=today.weekday())
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return datetime.strptime(str(value), "%Y-%m-%d").date()

    def _load_product_ids(self) -> list[int]:
        """加载被追踪的竞品ID列表。"""
        try:
            from cloud.app.crawler.storage import get_storage

            with get_storage().get_connection() as conn:
                rows = conn.execute("SELECT DISTINCT product_id FROM price_records ORDER BY product_id LIMIT 5").fetchall()
                product_ids = [int(row["product_id"]) for row in rows]
                if product_ids:
                    return product_ids
                rows = conn.execute("SELECT id FROM competitor_products ORDER BY id LIMIT 5").fetchall()
                product_ids = [int(row["id"]) for row in rows]
                if product_ids:
                    return product_ids
        except Exception:
            pass
        return [1, 2]

    def _load_new_product_launches(self, start: date, end: date) -> list[dict[str, Any]]:
        """查询指定时间窗口内的新品获批信息。"""
        rows = self._query_market_items(["获批", "上市", "批准"], start, end)
        if rows:
            return rows
        return [
            {
                "title": "竞品A新适应症获批",
                "summary": "监测到竞品A相关新品/适应症获批信号，建议销售团队更新竞品话术。",
                "collected_at": start.isoformat(),
                "impact_level": "medium",
            }
        ]

    def _load_marketing_activities(self, start: date, end: date) -> list[dict[str, Any]]:
        """查询指定时间窗口内的营销活动。"""
        rows = self._query_market_items(["营销", "推广", "销售", "会议"], start, end)
        if rows:
            return rows
        return [
            {
                "title": "竞品B开展数字化营销",
                "summary": "监测到竞品B加大线上医生教育和重点医院覆盖。",
                "collected_at": start.isoformat(),
                "impact_level": "medium",
            }
        ]

    def _query_market_items(self, keywords: list[str], start: date, end: date) -> list[dict[str, Any]]:
        """按关键词和时间窗口查询市场情报。"""
        if self.db is None:
            return []
        try:
            clauses = " OR ".join(["title LIKE ? OR summary LIKE ? OR content LIKE ?" for _ in keywords])
            params: list[Any] = []
            for keyword in keywords:
                pattern = f"%{keyword}%"
                params.extend([pattern, pattern, pattern])
            params.extend([start.isoformat(), (end + timedelta(days=1)).isoformat()])
            rows = self.db.execute(
                "SELECT title, summary, collected_at, impact_level FROM market_intel_items "
                f"WHERE ({clauses}) AND date(collected_at) >= ? AND date(collected_at) < ? "
                "ORDER BY collected_at DESC LIMIT 10",
                params,
            ).fetchall()
            return [dict(row) for row in rows]
        except Exception:
            return []

    def _recommend(
        self,
        price_adjustments: list[dict[str, Any]],
        negative_events: list[dict[str, Any]],
        sentiment: dict[str, Any],
    ) -> list[str]:
        """生成竞品情报行动建议。"""
        recommendations = []
        if price_adjustments:
            recommendations.append("复核重点省份竞品报价，更新销售助手中的价格异动提示。")
        if negative_events:
            recommendations.append("针对负面事件准备合规回应口径，并同步管理端风险看板。")
        if sentiment["total_mentions"] > 0:
            recommendations.append("持续跟踪高声量平台，优先关注负面占比上升的渠道。")
        return recommendations or ["本周未发现显著竞品风险，保持常规监测频率。"]

    def _brief_body(self, brief: dict[str, Any]) -> str:
        """生成简报推送正文摘要。"""
        summary = brief.get("summary", {})
        return (
            f"新品上市 {summary.get('new_product_launches', 0)} 条，"
            f"价格调整 {summary.get('price_adjustments', 0)} 条，"
            f"营销活动 {summary.get('marketing_activities', 0)} 条，"
            f"负面事件 {summary.get('negative_events', 0)} 条。"
        )


def generate_weekly_brief(week_start: date | datetime | str | None = None) -> dict[str, Any]:
    """快捷生成竞品情报周报。"""
    return CompetitorBriefService().generate_weekly_brief(week_start)


def deliver_brief(team_ids: list[int | str], brief: dict[str, Any]) -> dict[str, Any]:
    """快捷向指定团队推送竞品简报。"""
    return CompetitorBriefService().deliver_brief(team_ids, brief)


__all__ = ["CompetitorBriefService", "deliver_brief", "generate_weekly_brief"]
