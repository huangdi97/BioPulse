"""Core crawler engine for competitor intelligence collection."""

from __future__ import annotations

import asyncio
import inspect
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

import httpx

from cloud.app.crawler.data_sources import get_source_config
from cloud.app.crawler.proxy_pool import ProxyPool


@dataclass
class CrawlResult:
    """Normalized crawler response payload."""

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Crawler:
    """Simple httpx based crawler with proxy rotation and a Playwright render hook."""

    def __init__(
        self,
        proxy_pool: ProxyPool | None = None,
        timeout: float = 20.0,
        max_retries: int = 2,
    ) -> None:
        self.proxy_pool = proxy_pool or ProxyPool()
        self.timeout = timeout
        self.max_retries = max_retries

    # -- public API ------------------------------------------------------------

    def crawl(
        self,
        url: str,
        source_type: str,
        callback: Callable[[CrawlResult], Any] | None = None,
    ) -> CrawlResult:
        """Synchronously fetch a URL, dispatching to Playwright or httpx per source config.

        Args:
            url: Target URL to crawl.
            source_type: Source identifier (weibo, xiaohongshu, bidding, news).
            callback: Optional sync callback invoked with the result.

        Returns:
            CrawlResult with content, metadata, source, and timestamp.
        """
        config = get_source_config(source_type) if source_type in {"weibo", "xiaohongshu", "bidding", "news"} else None
        if config and config.render_required:
            content, metadata = self._render_with_playwright(url, source_type)
        else:
            content, metadata = self._fetch_http(url, config.headers if config else None)

        result = CrawlResult(
            content=content,
            metadata={
                "url": url,
                "source_type": source_type,
                **(config.metadata if config else {}),
                **metadata,
            },
            source=source_type,
        )
        if callback:
            callback(result)
        return result

    async def async_crawl(
        self,
        url: str,
        source_type: str,
        callback: Callable[[CrawlResult], Any] | None = None,
    ) -> CrawlResult:
        """Asynchronously fetch a URL, dispatching to Playwright or httpx per source config.

        Args:
            url: Target URL to crawl.
            source_type: Source identifier (weibo, xiaohongshu, bidding, news).
            callback: Optional async callback invoked with the result.

        Returns:
            CrawlResult with content, metadata, source, and timestamp.
        """
        config = get_source_config(source_type) if source_type in {"weibo", "xiaohongshu", "bidding", "news"} else None
        if config and config.render_required:
            content, metadata = self._render_with_playwright(url, source_type)
        else:
            content, metadata = await self._async_fetch_http(url, config.headers if config else None)
        result = CrawlResult(
            content=content,
            metadata={
                "url": url,
                "source_type": source_type,
                **(config.metadata if config else {}),
                **metadata,
            },
            source=source_type,
        )
        if callback:
            maybe_result = callback(result)
            if inspect.isawaitable(maybe_result):
                await maybe_result
        return result

    # -- HTTP fetch helpers ----------------------------------------------------

    def _fetch_http(self, url: str, headers: dict[str, str] | None = None) -> tuple[str, dict[str, Any]]:
        """Synchronous HTTP GET with proxy rotation and retry logic."""
        last_error: Exception | None = None
        attempts = self.max_retries + 1
        for attempt in range(1, attempts + 1):
            kwargs, proxy = self._prepare_request(headers)
            try:
                with httpx.Client(timeout=self.timeout, **kwargs) as client:
                    response = client.get(url)
                    if self._check_response_blocked(response, proxy):
                        if attempt < attempts:
                            time.sleep(self.proxy_pool.jitter(0.5))
                            continue
                    response.raise_for_status()
                    return self._build_response_result(response, attempt, proxy)
            except Exception as exc:
                last_error = exc
                self._check_error_rotate(exc, proxy)
                if attempt < attempts:
                    time.sleep(self.proxy_pool.jitter(0.5))
                    continue
                raise
        raise RuntimeError(f"Failed to crawl {url}") from last_error

    async def _async_fetch_http(self, url: str, headers: dict[str, str] | None = None) -> tuple[str, dict[str, Any]]:
        """Asynchronous HTTP GET with proxy rotation and retry logic."""
        last_error: Exception | None = None
        attempts = self.max_retries + 1
        for attempt in range(1, attempts + 1):
            kwargs, proxy = self._prepare_request(headers)
            try:
                async with httpx.AsyncClient(timeout=self.timeout, **kwargs) as client:
                    response = await client.get(url)
                    if self._check_response_blocked(response, proxy):
                        if attempt < attempts:
                            await asyncio.sleep(self.proxy_pool.jitter(0.5))
                            continue
                    response.raise_for_status()
                    return self._build_response_result(response, attempt, proxy)
            except Exception as exc:
                last_error = exc
                self._check_error_rotate(exc, proxy)
                if attempt < attempts:
                    await asyncio.sleep(self.proxy_pool.jitter(0.5))
                    continue
                raise
        raise RuntimeError(f"Failed to crawl {url}") from last_error

    def _prepare_request(self, headers: dict[str, str] | None) -> tuple[dict, str | None]:
        """Build client kwargs and extract the selected proxy URL."""
        kwargs = self.proxy_pool.build_client_kwargs(headers)
        return kwargs, kwargs.get("proxy")

    def _check_response_blocked(self, response: httpx.Response, proxy: str | None) -> bool:
        """Return True if the response indicates a block; report proxy failure if so."""
        if self.proxy_pool.should_rotate(response=response):
            self.proxy_pool.report_failure(proxy)
            return True
        return False

    def _check_error_rotate(self, error: Exception, proxy: str | None) -> None:
        """Report proxy failure if the error type warrants rotation."""
        if self.proxy_pool.should_rotate(error=error):
            self.proxy_pool.report_failure(proxy)

    @staticmethod
    def _build_response_result(response: httpx.Response, attempt: int, proxy: str | None) -> tuple[str, dict[str, Any]]:
        """Build the (content, metadata) tuple from a successful response."""
        return response.text, {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "attempt": attempt,
            "proxy": proxy or "",
        }

    # -- Playwright hook -------------------------------------------------------

    def _render_with_playwright(self, url: str, source_type: str) -> tuple[str, dict[str, Any]]:
        """Reserved Playwright render hook; falls back to httpx until browser runtime is enabled."""
        content, metadata = self._fetch_http(url)
        metadata["render_engine"] = "httpx_fallback"
        metadata["render_requested"] = True
        metadata["render_source_type"] = source_type
        return content, metadata


__all__ = ["CrawlResult", "Crawler"]
