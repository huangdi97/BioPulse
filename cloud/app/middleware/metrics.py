"""Prometheus 监控中间件 — 受 ENABLE_METRICS 开关控制。"""

import logging
import os

from prometheus_client import Counter, Histogram, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator

logger = logging.getLogger("cloud")

_enabled = os.getenv("ENABLE_METRICS", "false").lower() in ("1", "true", "yes")

request_latency_seconds = Histogram(
    "request_latency_seconds",
    "HTTP 请求延迟（秒）",
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
)

agent_execution_latency = Histogram(
    "agent_execution_latency",
    "Agent 执行延迟（秒）",
    ["agent_name"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

agent_token_consumption = Counter(
    "agent_token_consumption",
    "Agent Token 消耗总量",
    ["agent_name", "model"],
)

http_requests_total = Counter(
    "http_requests_total",
    "HTTP 请求总数",
    ["method", "endpoint", "status"],
)


def setup_metrics(app) -> Instrumentator | None:
    if not _enabled:
        logger.info("Metrics disabled (ENABLE_METRICS != true)")
        return None
    logger.info("Prometheus metrics enabled on /metrics")
    return Instrumentator().instrument(app).expose(app)


def metrics_payload() -> str:
    return generate_latest().decode("utf-8")
