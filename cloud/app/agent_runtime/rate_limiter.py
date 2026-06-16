"""Agent 级速率限制，支持按 Agent、按用户、按端限流。"""

import logging
import time
from threading import Lock

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    def __init__(self, key: str, limit: int, window: int, retry_after: float):
        self.key = key
        self.limit = limit
        self.window = window
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded for '{key}': {limit} per {window}s, retry after {retry_after:.0f}s")


class RateLimiter:
    """Agent 级速率限制，支持按 Agent、按用户、按端限流。

    默认限制：
        - 每个 Agent 每分钟最多 30 次 LLM 调用
        - 每个用户每分钟最多 60 次 Agent 调用
    超出返回 RateLimitExceeded，包含 retry_after 信息。
    """

    DEFAULTS: dict[str, tuple[int, int]] = {
        "agent_llm": (30, 60),
        "user_agent": (60, 60),
    }

    def __init__(self):
        self._lock = Lock()
        self._limits: dict[str, tuple[int, int]] = dict(self.DEFAULTS)
        self._windows: dict[str, list[float]] = {}

    def set_limit(self, key: str, max_calls: int, window_seconds: int) -> None:
        """set limit."""
        with self._lock:
            self._limits[key] = (max_calls, window_seconds)

    def check(self, key: str) -> bool:
        """check."""
        now = time.time()
        max_calls, window = self._limits.get(key, (0, 0))
        if max_calls <= 0:
            return True
        with self._lock:
            calls = self._windows.setdefault(key, [])
            cutoff = now - window
            calls[:] = [t for t in calls if t > cutoff]
            if len(calls) >= max_calls:
                return False
            calls.append(now)
        return True

    def check_or_raise(self, key: str) -> None:
        """check or raise."""
        now = time.time()
        max_calls, window = self._limits.get(key, (0, 0))
        if max_calls <= 0:
            return
        with self._lock:
            calls = self._windows.setdefault(key, [])
            cutoff = now - window
            calls[:] = [t for t in calls if t > cutoff]
            if len(calls) >= max_calls:
                oldest = calls[0] if calls else now
                retry_after = window - (now - oldest)
                raise RateLimitExceeded(key, max_calls, window, retry_after)
            calls.append(now)

    def get_remaining(self, key: str) -> int:
        """get remaining."""
        now = time.time()
        max_calls, window = self._limits.get(key, (0, 0))
        if max_calls <= 0:
            return 0
        with self._lock:
            calls = self._windows.setdefault(key, [])
            cutoff = now - window
            calls[:] = [t for t in calls if t > cutoff]
            return max(0, max_calls - len(calls))

    def reset(self, key: str | None = None) -> None:
        """reset."""
        with self._lock:
            if key:
                self._windows.pop(key, None)
            else:
                self._windows.clear()

    @property
    def limits(self) -> dict[str, tuple[int, int]]:
        return dict(self._limits)
