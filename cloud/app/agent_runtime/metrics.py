"""Agent Runtime Prometheus Metrics — 请求量、错误率、延迟、活跃数、Token消耗。"""

import sqlite3
from datetime import datetime, timedelta

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


def _get_db() -> sqlite3.Connection:
    from cloud.app.agent_database import AGENT_DB_PATH

    conn = sqlite3.connect(AGENT_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_agent_metrics(agent_name: str, time_range_hours: int = 24) -> dict:
    cutoff = (datetime.utcnow() - timedelta(hours=time_range_hours)).strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = _get_db()
    except Exception:
        return {"total_calls": 0, "avg_duration_ms": 0, "total_cost": 0.0, "error_rate": 0.0}

    try:
        trace = conn.execute(
            "SELECT COUNT(*) as total_calls, "
            "COALESCE(AVG(NULLIF(total_duration_ms, 0)), 0) as avg_duration_ms, "
            "COALESCE(SUM(CASE WHEN status NOT IN ('success','completed') THEN 1 ELSE 0 END) * 1.0 "
            "/ NULLIF(COUNT(*), 0), 0) as error_rate "
            "FROM agent_traces WHERE agent_name=? AND started_at >= ? AND started_at != ''",
            (agent_name, cutoff),
        ).fetchone()

        cost_row = conn.execute(
            "SELECT COALESCE(SUM(cost), 0) as total_cost FROM agent_cost_tracking WHERE agent_name=? AND timestamp >= ?",
            (agent_name, cutoff),
        ).fetchone()

        return {
            "total_calls": trace["total_calls"],
            "avg_duration_ms": round(trace["avg_duration_ms"], 2),
            "total_cost": round(cost_row["total_cost"], 4),
            "error_rate": round(trace["error_rate"], 4),
        }
    finally:
        conn.close()


def get_runtime_health() -> dict:
    components = {
        "database": {"status": "unknown"},
        "runtime_logs": {"status": "unknown"},
        "prometheus_metrics": {
            "status": "healthy",
            "metrics_available": [
                "agent_requests_total",
                "agent_llm_duration",
                "agent_active_count",
                "agent_tokens_total",
            ],
        },
    }

    try:
        conn = _get_db()
    except Exception:
        components["database"] = {"status": "unhealthy", "connectivity": "error"}
        components["runtime_logs"] = {"status": "unhealthy"}
        return components

    try:
        conn.execute("SELECT 1 FROM agent_traces LIMIT 1")
        components["database"] = {"status": "healthy", "connectivity": "ok"}
    except Exception:
        components["database"] = {"status": "unhealthy", "connectivity": "error"}

    try:
        conn.execute("SELECT 1 FROM agent_runtime_logs LIMIT 1")
        components["runtime_logs"] = {"status": "healthy"}
    except Exception:
        components["runtime_logs"] = {"status": "unhealthy"}

    conn.close()
    return components


def get_cost_breakdown(period: str = "daily") -> dict:
    try:
        conn = _get_db()
    except Exception:
        return {"items": [], "total_tokens": 0, "total_cost": 0.0}

    try:
        if period == "hourly":
            group_expr = "strftime('%Y-%m-%d %H:00', timestamp)"
        else:
            group_expr = "DATE(timestamp)"

        rows = conn.execute(
            f"SELECT {group_expr} as period, agent_name, "
            "SUM(input_tokens) as input_tokens, SUM(output_tokens) as output_tokens, "
            "SUM(input_tokens + output_tokens) as total_tokens, SUM(cost) as cost "
            "FROM agent_cost_tracking "
            "GROUP BY period, agent_name ORDER BY period DESC"
        ).fetchall()

        items = []
        total_tokens = 0
        total_cost = 0.0
        for r in rows:
            items.append(
                {
                    "period": r["period"],
                    "agent_name": r["agent_name"],
                    "input_tokens": r["input_tokens"],
                    "output_tokens": r["output_tokens"],
                    "total_tokens": r["total_tokens"],
                    "cost": round(r["cost"], 4),
                }
            )
            total_tokens += r["total_tokens"]
            total_cost += r["cost"]

        return {
            "items": items,
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 4),
        }
    finally:
        conn.close()


def record_success(agent_name: str) -> None:
    """记录一次成功的 Agent 调用。"""
    agent_requests_total.labels(agent_name=agent_name, status="success").inc()


def record_failure(agent_name: str) -> None:
    """记录一次失败的 Agent 调用。"""
    agent_requests_total.labels(agent_name=agent_name, status="failure").inc()


def get_success_rate(agent_name: str, hours: int = 24) -> float:
    """获取指定 Agent 最近 N 小时的成功率 (0-1)。"""
    try:
        conn = _get_db()
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        row = conn.execute(
            "SELECT "
            "COALESCE(SUM(CASE WHEN status IN ('success','completed') THEN 1 ELSE 0 END), 0) as success,"
            "COUNT(*) as total FROM agent_traces WHERE agent_name=? AND started_at >= ?",
            (agent_name, cutoff),
        ).fetchone()
        conn.close()
        if row["total"] == 0:
            return 1.0
        return row["success"] / row["total"]
    except Exception:
        return 1.0


def get_error_rate(agent_name: str, hours: int = 24) -> float:
    """获取指定 Agent 最近 N 小时的错误率 (0-1)。"""
    return 1.0 - get_success_rate(agent_name, hours)
