"""Data source configuration for competitor crawler."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SourceConfig:
    """Configuration for a single crawl source."""

    name: str
    url_template: str
    crawl_frequency_minutes: int
    anti_scrape: str  # proxy | headers | captcha | none
    render_required: bool = False
    headers: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


_SOURCES: dict[str, SourceConfig] = {
    "douyin": SourceConfig(
        name="抖音",
        url_template="https://www.douyin.com/search/{keyword}?type=general",
        crawl_frequency_minutes=1440,
        anti_scrape="proxy",
        render_required=True,
        headers={
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
            "Accept": "text/html,application/json,*/*",
        },
    ),
    "xiaohongshu": SourceConfig(
        name="小红书",
        url_template="https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web",
        crawl_frequency_minutes=1440,
        anti_scrape="proxy",
        render_required=True,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/json,*/*",
        },
    ),
    "weibo": SourceConfig(
        name="微博",
        url_template="https://s.weibo.com/weibo?q={keyword}&typeall=1",
        crawl_frequency_minutes=720,
        anti_scrape="headers",
        render_required=False,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://weibo.com/",
        },
    ),
    "bidding": SourceConfig(
        name="招标信息",
        url_template="https://www.chinabidding.com.cn/search?q={keyword}",
        crawl_frequency_minutes=1440,
        anti_scrape="headers",
        render_required=False,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; Crawler/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        },
    ),
    "news": SourceConfig(
        name="行业新闻",
        url_template="https://news.google.com/search?q={keyword}&hl=zh-CN&gl=CN",
        crawl_frequency_minutes=1440,
        anti_scrape="proxy",
        render_required=False,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
        },
    ),
}


def get_source_config(source_type: str) -> SourceConfig | None:
    """Return the config for a named source, or None if unknown."""
    return _SOURCES.get(source_type)


def list_sources() -> dict[str, SourceConfig]:
    """Return a copy of all source configs."""
    return dict(_SOURCES)
