"""Agent Runtime Prometheus Metrics — 请求量、错误率、延迟、活跃数、Token消耗。"""

from prometheus_client import Counter, Gauge, Histogram, generate_latest

agent_requests_total = Counter(
    "agent_requests_total",
    "总请求数",
    ["agent_name", "status"],
)

agent_llm_duration = Histogram(
    "agent_llm_duration_seconds",
    "LLM调用耗时",
    ["agent_name", "model"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

agent_active_count = Gauge(
    "agent_active_count",
    "当前活跃Agent数",
    ["agent_name"],
)

agent_tokens_total = Counter(
    "agent_tokens_total",
    "Token消耗总量",
    ["agent_name"],
)


def get_metrics() -> str:
    """get metrics."""
    return generate_latest().decode("utf-8")
