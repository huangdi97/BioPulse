"""Crawler engine core — async HTTP fetching with proxy rotation and UA randomisation."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

import httpx

from cloud.app.competitor_crawler.sources import SourceConfig, get_source_config

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15 Mobile/15E148",
    "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile",
]

PROXY_LIST = [
    None,
]


@dataclass
class CrawlResult:
    """Normalized crawl result."""

    content: str
    source: str
    url: str
    success: bool = True
    status_code: int = 200
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CrawlerEngine:
    """Async crawler engine with proxy rotation and UA randomisation."""

    def __init__(self, timeout: float = 30.0, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self._proxy_index = 0

    def _rotate_proxy(self) -> str | None:
        proxy = PROXY_LIST[self._proxy_index % max(len(PROXY_LIST), 1)]
        self._proxy_index += 1
        return proxy

    def _random_ua(self) -> str:
        return random.choice(USER_AGENTS)

    def _build_headers(self, config: SourceConfig | None) -> dict[str, str]:
        headers = {"User-Agent": self._random_ua(), "Accept": "*/*"}
        if config and config.headers:
            headers.update(config.headers)
        return headers

    async def crawl(self, url: str, source_type: str = "news", callback: Callable[[CrawlResult], Any] | None = None) -> CrawlResult:
        """Fetch a single URL asynchronously with retries."""
        config = get_source_config(source_type)
        headers = self._build_headers(config)

        for attempt in range(1, self.max_retries + 1):
            proxy = self._rotate_proxy()
            try:
                transport = httpx.AsyncHTTPProxy(proxy) if proxy else None
                async with httpx.AsyncClient(transport=transport, timeout=self.timeout) as client:
                    resp = await client.get(url, headers=headers, follow_redirects=True)
                    resp.raise_for_status()
                    result = CrawlResult(
                        content=resp.text,
                        source=source_type,
                        url=url,
                        status_code=resp.status_code,
                        metadata={"attempt": attempt, "proxy": proxy or "direct", "headers": dict(resp.headers)},
                    )
                    if callback:
                        cb = callback(result)
                        if asyncio.iscoroutine(cb):
                            await cb
                    return result
            except Exception as exc:
                if attempt < self.max_retries:
                    await asyncio.sleep(random.uniform(1.0, 3.0))
                else:
                    return CrawlResult(content="", source=source_type, url=url, success=False, error=str(exc), status_code=0)

        return CrawlResult(content="", source=source_type, url=url, success=False, error="max retries exceeded", status_code=0)

    async def crawl_many(self, urls: list[tuple[str, str]], concurrency: int = 5) -> list[CrawlResult]:
        """Crawl multiple URLs concurrently with a semaphore."""
        sem = asyncio.Semaphore(concurrency)

        async def _bound(url: str, source: str) -> CrawlResult:
            async with sem:
                return await self.crawl(url, source)

        tasks = [_bound(url, src) for url, src in urls]
        return await asyncio.gather(*tasks)
