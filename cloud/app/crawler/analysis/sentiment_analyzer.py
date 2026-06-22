"""Public opinion and sentiment analysis for competitor intelligence."""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from typing import Any

from cloud.app.crawler.analysis import load_public_opinions

logger = logging.getLogger(__name__)

POSITIVE_WORDS = {
    "利好",
    "积极",
    "增长",
    "领先",
    "获批",
    "改善",
    "突破",
    "好评",
    "positive",
    "good",
    "great",
    "strong",
    "success",
}
NEGATIVE_WORDS = {
    "负面",
    "下降",
    "投诉",
    "风险",
    "不稳定",
    "降价",
    "召回",
    "质疑",
    "negative",
    "bad",
    "risk",
    "weak",
    "complaint",
}


class SentimentAnalyzer:
    """Analyze sentiment distribution, volume trend and platform mentions."""

    def __init__(self, storage: Any | None = None) -> None:
        self.storage = storage

    def analyze(self, keyword: str, platform: str | None = None, days: int = 7) -> dict[str, Any]:
        """Analyze sentiment for a keyword over the given window.

        Args:
            keyword: Search keyword.
            platform: Optional platform filter (None = all platforms).
            days: Number of days to analyze.

        Returns:
            Dict with sentiment distribution, ratio, daily trend, volume comparison, and top mentions.
        """
        platforms = [platform] if platform else None
        mentions = load_public_opinions(keyword, days=days, platforms=platforms, storage=self.storage)
        enriched = []
        for mention in mentions:
            sentiment = self._classify(mention)
            enriched.append({**mention, "sentiment": sentiment})

        distribution = Counter(item["sentiment"] for item in enriched)
        by_platform: dict[str, Counter] = defaultdict(Counter)
        by_date: dict[str, Counter] = defaultdict(Counter)
        for item in enriched:
            by_platform[item["platform"]][item["sentiment"]] += 1
            by_date[item["publish_date"]]["mentions"] += 1
            by_date[item["publish_date"]][item["sentiment"]] += 1

        total_mentions = len(enriched)
        return {
            "keyword": keyword,
            "platform": platform or "all",
            "days": days,
            "total_mentions": total_mentions,
            "sentiment_distribution": {
                "positive": distribution.get("positive", 0),
                "neutral": distribution.get("neutral", 0),
                "negative": distribution.get("negative", 0),
            },
            "sentiment_ratio": self._ratio(distribution, total_mentions),
            "trend": self._build_trend_list(by_date),
            "volume_comparison": self._build_volume_comparison(by_platform),
            "top_mentions": enriched[-5:],
        }

    def track_mentions(self, keyword: str, platforms: list[str]) -> dict[str, Any]:
        """Track mentions per platform for a keyword, aggregating sentiment per platform.

        Args:
            keyword: Search keyword.
            platforms: List of platform names to track individually.

        Returns:
            Dict with total_mentions and per-platform sentiment breakdowns.
        """
        all_mentions = load_public_opinions(keyword, days=7, platforms=None, storage=self.storage)
        by_platform_mentions: dict[str, list[dict]] = defaultdict(list)
        for mention in all_mentions:
            by_platform_mentions[mention["platform"]].append(mention)

        result: dict[str, Any] = {"keyword": keyword, "platforms": []}
        for platform in platforms:
            mentions = by_platform_mentions.get(platform, [])
            enriched = []
            for mention in mentions:
                sentiment = self._classify(mention)
                enriched.append({**mention, "sentiment": sentiment})

            by_date: dict[str, Counter] = defaultdict(Counter)
            for item in enriched:
                by_date[item["publish_date"]]["mentions"] += 1
                by_date[item["publish_date"]][item["sentiment"]] += 1

            result["platforms"].append(self._build_platform_result(platform, mentions))

        result["total_mentions"] = sum(item["mentions"] for item in result["platforms"])
        return result

    def _build_platform_result(self, platform, mentions):
        enriched = []
        for mention in mentions:
            sentiment = self._classify(mention)
            enriched.append({**mention, "sentiment": sentiment})

        distribution = Counter(item["sentiment"] for item in enriched)
        by_date = defaultdict(Counter)
        for item in enriched:
            by_date[item["publish_date"]]["mentions"] += 1
            by_date[item["publish_date"]][item["sentiment"]] += 1

        total_mentions = len(enriched)
        return {
            "platform": platform,
            "mentions": total_mentions,
            "sentiment_distribution": {
                "positive": distribution.get("positive", 0),
                "neutral": distribution.get("neutral", 0),
                "negative": distribution.get("negative", 0),
            },
            "trend": self._build_trend_list(by_date),
        }

    # -- internal helpers ------------------------------------------------------

    def _classify(self, mention: dict[str, Any]) -> str:
        # Classify sentiment: use pre-labeled value, then keyword counts, then TextBlob fallback.
        provided = str(mention.get("sentiment") or "").lower()
        if provided in {"positive", "neutral", "negative"}:
            return provided

        text = f"{mention.get('title', '')} {mention.get('content', '')}".lower()
        positive_hits = sum(1 for word in POSITIVE_WORDS if re.search(r"\b" + re.escape(word) + r"\b", text))
        negative_hits = sum(1 for word in NEGATIVE_WORDS if re.search(r"\b" + re.escape(word) + r"\b", text))
        if positive_hits > negative_hits:
            return "positive"
        if negative_hits > positive_hits:
            return "negative"

        try:
            from textblob import TextBlob

            polarity = TextBlob(text).sentiment.polarity
            if polarity > 0.1:
                return "positive"
            if polarity < -0.1:
                return "negative"
        except Exception:
            logger.warning("情感分析异常", exc_info=True)
        return "neutral"

    def _ratio(self, distribution: Counter, total: int) -> dict[str, float]:
        # Compute sentiment ratios from distribution counts and total.
        if total <= 0:
            return {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
        return {
            "positive": round(distribution.get("positive", 0) / total, 4),
            "neutral": round(distribution.get("neutral", 0) / total, 4),
            "negative": round(distribution.get("negative", 0) / total, 4),
        }

    @staticmethod
    def _build_trend_list(by_date):
        return [
            {
                "date": day,
                "mentions": counts.get("mentions", 0),
                "positive": counts.get("positive", 0),
                "neutral": counts.get("neutral", 0),
                "negative": counts.get("negative", 0),
            }
            for day, counts in sorted(by_date.items())
        ]

    @staticmethod
    def _build_volume_comparison(by_platform):
        return [
            {
                "platform": name,
                "mentions": sum(counts.values()),
                "positive": counts.get("positive", 0),
                "neutral": counts.get("neutral", 0),
                "negative": counts.get("negative", 0),
            }
            for name, counts in sorted(by_platform.items(), key=lambda item: sum(item[1].values()), reverse=True)
        ]


def analyze(keyword: str, platform: str | None = None, days: int = 7) -> dict[str, Any]:
    """Convenience function: run sentiment analysis with a default analyzer."""
    return SentimentAnalyzer().analyze(keyword, platform=platform, days=days)


def track_mentions(keyword: str, platforms: list[str]) -> dict[str, Any]:
    """Convenience function: track per-platform mentions with a default analyzer."""
    return SentimentAnalyzer().track_mentions(keyword, platforms)


__all__ = ["SentimentAnalyzer", "analyze", "track_mentions"]
