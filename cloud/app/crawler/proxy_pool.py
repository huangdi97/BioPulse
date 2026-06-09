"""Proxy and User-Agent rotation for crawler requests."""

from __future__ import annotations

import itertools
import random
from collections.abc import Iterable

import httpx

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
]


class ProxyPool:
    """Rotate User-Agent and proxy settings, with basic anti-crawler detection."""

    block_status_codes = {403, 407, 418, 429, 451, 503}
    block_keywords = ("captcha", "验证码", "访问过于频繁", "forbidden", "blocked", "风控")

    def __init__(
        self,
        proxies: Iterable[str] | None = None,
        user_agents: Iterable[str] | None = None,
    ) -> None:
        self._proxies = list(proxies or [])
        self._user_agents = list(user_agents or DEFAULT_USER_AGENTS)
        self._proxy_cycle = itertools.cycle(self._proxies) if self._proxies else None
        self._ua_cycle = itertools.cycle(self._user_agents)
        self._dead_proxies: set[str] = set()

    def next_user_agent(self) -> str:
        """Return the next User-Agent from the rotation cycle."""
        return next(self._ua_cycle)

    def next_proxy(self) -> str | None:
        """Return the next non-dead proxy URL, or None if no proxies configured."""
        if not self._proxy_cycle:
            return None
        for _ in range(max(len(self._proxies), 1)):
            proxy = next(self._proxy_cycle)
            if proxy not in self._dead_proxies:
                return proxy
        self._dead_proxies.clear()
        return next(self._proxy_cycle)

    def build_headers(self, headers: dict[str, str] | None = None) -> dict[str, str]:
        """Build request headers with a rotated User-Agent, merging caller overrides."""
        merged = {
            "User-Agent": self.next_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        if headers:
            merged.update(headers)
        return merged

    def build_client_kwargs(self, headers: dict[str, str] | None = None) -> dict:
        """Build keyword arguments for httpx Client, including headers and optional proxy."""
        kwargs = {"headers": self.build_headers(headers), "follow_redirects": True}
        proxy = self.next_proxy()
        if proxy:
            kwargs["proxy"] = proxy
        return kwargs

    def report_failure(self, proxy: str | None) -> None:
        """Mark a proxy as dead so it is skipped on subsequent rotations."""
        if proxy:
            self._dead_proxies.add(proxy)

    def should_rotate(self, response: httpx.Response | None = None, error: Exception | None = None) -> bool:
        """Return True if the response or error indicates a proxy should be rotated.

        Args:
            response: Optional httpx response to inspect for block signals.
            error: Optional exception to inspect for connectivity issues.

        Returns:
            True if the current proxy should be rotated out.
        """
        if error is not None:
            return isinstance(error, (httpx.ProxyError, httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout))
        if response is None:
            return False
        if response.status_code in self.block_status_codes:
            return True
        for header_name in ("x-blocked", "x-captcha", "x-anti-bot", "cf-ray", "server"):
            header_val = response.headers.get(header_name, "")
            if any(keyword.lower() in header_val.lower() for keyword in self.block_keywords):
                return True
        content = response.content[:2000].decode(errors="ignore").lower()
        return any(keyword.lower() in content for keyword in self.block_keywords)

    def jitter(self, base_seconds: float) -> float:
        """Return base_seconds with a small random jitter to avoid synchronized retries."""
        return base_seconds + random.uniform(0, min(base_seconds, 1.0))


__all__ = ["DEFAULT_USER_AGENTS", "ProxyPool"]
