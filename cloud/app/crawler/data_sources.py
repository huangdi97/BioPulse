"""Crawler source configuration for competitor intelligence platforms."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceConfig:
    """Declarative crawl rules for a data source."""

    name: str
    source_type: str
    base_url: str
    search_path: str
    render_required: bool = False
    rate_limit_seconds: float = 1.0
    max_retries: int = 2
    timeout_seconds: float = 20.0
    headers: dict[str, str] = field(default_factory=dict)
    selectors: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def build_search_url(self, keyword: str, page: int = 1) -> str:
        return self.base_url.rstrip("/") + self.search_path.format(keyword=keyword, page=page)


DATA_SOURCES: dict[str, SourceConfig] = {
    "weibo": SourceConfig(
        name="weibo",
        source_type="social",
        base_url="https://s.weibo.com",
        search_path="/weibo?q={keyword}&page={page}",
        render_required=True,
        rate_limit_seconds=2.0,
        selectors={
            "item": ".card-wrap",
            "title": ".content a",
            "content": ".content p",
            "publish_date": ".from a",
        },
        metadata={"platform": "微博", "focus": "public_opinion"},
    ),
    "xiaohongshu": SourceConfig(
        name="xiaohongshu",
        source_type="social",
        base_url="https://www.xiaohongshu.com",
        search_path="/search_result?keyword={keyword}&page={page}",
        render_required=True,
        rate_limit_seconds=2.5,
        selectors={
            "item": ".note-item",
            "title": ".title",
            "content": ".content",
            "publish_date": ".date",
        },
        metadata={"platform": "小红书", "focus": "public_opinion"},
    ),
    "bidding": SourceConfig(
        name="bidding",
        source_type="bidding",
        base_url="https://www.ccgp.gov.cn",
        search_path="/search?searchtype=1&page_index={page}&kw={keyword}",
        render_required=False,
        rate_limit_seconds=1.5,
        selectors={
            "item": ".vT-srch-result-list-bid li",
            "title": "a",
            "publish_date": ".span-2022",
            "province": ".source",
        },
        metadata={"platform": "招标公告", "focus": "bidding"},
    ),
    "news": SourceConfig(
        name="news",
        source_type="news",
        base_url="https://news.baidu.com",
        search_path="/ns?word={keyword}&pn={page}",
        render_required=False,
        rate_limit_seconds=1.0,
        selectors={
            "item": ".result",
            "title": "h3 a",
            "content": ".c-summary",
            "publish_date": ".c-author",
        },
        metadata={"platform": "新闻", "focus": "market_news"},
    ),
}


def get_source_config(source: str) -> SourceConfig:
    """Return a source config by name, raising a clear error for unknown sources."""

    try:
        return DATA_SOURCES[source]
    except KeyError as exc:
        known = ", ".join(sorted(DATA_SOURCES))
        raise ValueError(f"Unknown crawler source '{source}'. Known sources: {known}") from exc


__all__ = ["DATA_SOURCES", "SourceConfig", "get_source_config"]
