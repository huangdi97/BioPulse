"""Agent runtime Prometheus metrics for monitoring call volume, latency, token usage, and tool calls."""

from prometheus_client import Counter, Histogram

agent_calls_total = Counter(
    "agent_calls_total",
    "Total number of agent calls",
    ["agent_key", "status"],
)

agent_call_duration_seconds = Histogram(
    "agent_call_duration_seconds",
    "Agent call duration in seconds",
    ["agent_key"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0),
)

agent_token_consumed_total = Counter(
    "agent_token_consumed_total",
    "Total tokens consumed by agent calls",
    ["agent_key", "model"],
)

agent_tool_calls_total = Counter(
    "agent_tool_calls_total",
    "Total number of tool calls made by agents",
    ["agent_key", "tool_name"],
)
