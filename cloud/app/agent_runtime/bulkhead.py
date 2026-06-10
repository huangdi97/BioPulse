"""Bulkhead 隔离 — Agent 级资源隔离，限制每个 Agent 的最大并发执行数。"""

import logging
import threading

logger = logging.getLogger(__name__)


class Bulkhead:
    """Agent 级资源隔离，使用 threading.Semaphore 限制每个 Agent 的并发执行数。

    限制：
        - 每个 Agent 最多同时 3 个执行实例
        - 超过时排队等待（默认 30 秒后超时）
    """

    DEFAULT_MAX_CONCURRENT = 3
    DEFAULT_TIMEOUT = 30.0

    def __init__(self):
        self._semaphores: dict[str, threading.Semaphore] = {}
        self._lock = threading.Lock()

    def get_semaphore(self, agent_name: str, max_concurrent: int | None = None) -> threading.Semaphore:
        if max_concurrent is None:
            max_concurrent = self.DEFAULT_MAX_CONCURRENT
        with self._lock:
            if agent_name not in self._semaphores:
                self._semaphores[agent_name] = threading.Semaphore(max_concurrent)
            return self._semaphores[agent_name]

    def acquire(self, agent_name: str, timeout: float | None = None) -> bool:
        sem = self.get_semaphore(agent_name)
        if timeout is None:
            timeout = self.DEFAULT_TIMEOUT
        acquired = sem.acquire(blocking=True, timeout=timeout)
        if acquired:
            logger.debug("Bulkhead acquired for agent %s", agent_name)
        else:
            logger.warning("Bulkhead timeout for agent %s after %.1fs", agent_name, timeout)
        return acquired

    def release(self, agent_name: str) -> None:
        sem = self._semaphores.get(agent_name)
        if sem:
            sem.release()
            logger.debug("Bulkhead released for agent %s", agent_name)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
