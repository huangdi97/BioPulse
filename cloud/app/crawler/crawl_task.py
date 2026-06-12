"""任务定义和配置类。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ScheduledCrawlerJob:
    """A single scheduled crawler job definition."""

    id: str
    source: str
    interval: int
    max_pages: int
    keywords: list[str]
    paused: bool = False
    next_run_time: datetime | None = None


__all__ = ["ScheduledCrawlerJob"]
