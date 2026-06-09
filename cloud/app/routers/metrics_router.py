"""内存指标收集器与 /metrics 端点。"""

import time
from threading import Lock

from fastapi import APIRouter


class MetricsCollector:
    """单例内存指标收集器，记录请求计数、状态码分布、方法分布与延迟。"""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    obj = super().__new__(cls)
                    obj._total_requests = 0
                    obj._status_counts: dict[int, int] = {}
                    obj._method_counts: dict[str, int] = {}
                    obj._latency_buckets: list[float] = []
                    obj._recent_timestamps: list[float] = []
                    obj._data_lock = Lock()
                    cls._instance = obj
        return cls._instance

    def increment(self, method: str, status: int, duration_ms: float) -> None:
        with self._data_lock:
            self._total_requests += 1

            key = int(status)
            self._status_counts[key] = self._status_counts.get(key, 0) + 1

            self._method_counts[method] = self._method_counts.get(method, 0) + 1

            self._latency_buckets.append(float(duration_ms))
            if len(self._latency_buckets) > 1000:
                self._latency_buckets = self._latency_buckets[-1000:]

            self._recent_timestamps.append(time.time())

    def get_metrics(self) -> dict:
        with self._data_lock:
            buckets = sorted(self._latency_buckets) if self._latency_buckets else []
            total = self._total_requests

            def _percentile(p: float, lst: list[float]) -> float:
                if not lst:
                    return 0.0
                k = (len(lst) - 1) * p / 100.0
                f = int(k)
                c = k - f
                if f + 1 < len(lst):
                    return round(lst[f] + c * (lst[f + 1] - lst[f]), 2)
                return round(lst[f], 2)

            now = time.time()
            recent_count = sum(1 for ts in self._recent_timestamps if now - ts <= 60)
            self._recent_timestamps = [ts for ts in self._recent_timestamps if now - ts <= 60]

            return {
                "total_requests": total,
                "status_counts": dict(self._status_counts),
                "method_counts": dict(self._method_counts),
                "latency_p50_ms": _percentile(50, buckets),
                "latency_p95_ms": _percentile(95, buckets),
                "latency_p99_ms": _percentile(99, buckets),
                "requests_last_minute": recent_count,
            }


router = APIRouter(tags=["monitoring"])


@router.get("/metrics", tags=["monitoring"])
def get_metrics():
    mc = MetricsCollector()
    return mc.get_metrics()
