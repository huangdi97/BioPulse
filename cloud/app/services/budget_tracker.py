"""Token budget usage tracking — record, report, and alert on consumption."""

import sqlite3
from datetime import datetime, timedelta, timezone

from cloud.app.database import DB_PATH


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class BudgetTracker:
    """Tracks actual token usage per user per model and generates alerts."""

    def record_usage(self, user_id: int, model: str, tokens: int, cost: float) -> dict:
        """记录一次模型Token用量并刷新当日预算聚合。

        Args:
            user_id: 用户ID。
            model: 模型名称。
            tokens: 本次调用消耗的Token数量。
            cost: 本次调用成本。

        Returns:
            已记录用量的摘要字典。

        Raises:
            sqlite3.Error: 当用量或预算表写入失败时抛出。
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        now = datetime.now(timezone.utc).isoformat()
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO token_usage (user_id, model, tokens, cost, usage_date, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, model, tokens, cost, today, now),
            )
            conn.execute(
                "INSERT OR REPLACE INTO token_budget (user_id, model, daily_used, alert_sent, updated_at) "
                "VALUES (?, ?, "
                "  COALESCE((SELECT SUM(tokens) FROM token_usage WHERE user_id=? AND model=? AND usage_date=?), 0), "
                "  0, ?)",
                (user_id, model, user_id, model, today, now),
            )
            conn.execute("DELETE FROM token_budget WHERE rowid NOT IN (SELECT MAX(rowid) FROM token_budget GROUP BY user_id, model)")
            conn.commit()
        finally:
            conn.close()
        return {
            "user_id": user_id,
            "model": model,
            "tokens": tokens,
            "cost": cost,
            "usage_date": today,
        }

    def get_usage_report(self, user_id: int, days: int = 30) -> list:
        """查询用户在最近一段时间内的Token用量报表。

        Args:
            user_id: 用户ID。
            days: 向前统计的天数。

        Returns:
            按日期和模型聚合的Token、成本和调用次数列表。

        Raises:
            sqlite3.Error: 当用量查询失败时抛出。
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT usage_date, model, SUM(tokens) AS total_tokens, SUM(cost) AS total_cost, "
                "COUNT(*) AS call_count "
                "FROM token_usage WHERE user_id=? AND usage_date>=? "
                "GROUP BY usage_date, model ORDER BY usage_date DESC, model",
                (user_id, cutoff),
            ).fetchall()
        finally:
            conn.close()
        return [dict(r) for r in rows]

    def get_alerts(self, configs: list[dict]) -> list:
        """根据预算配置计算今日用量告警。

        Args:
            configs: 用户模型维度的预算配置列表。

        Returns:
            超过阈值的告警列表。

        Raises:
            sqlite3.Error: 当今日用量查询失败时抛出。
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if not configs:
            return []

        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT user_id, model, COALESCE(SUM(tokens), 0) AS total "
                "FROM token_usage WHERE usage_date=? "
                "GROUP BY user_id, model",
                (today,),
            ).fetchall()
            usage_map = {(r["user_id"], r["model"]): r["total"] for r in rows}

            alerts = []
            for cfg in configs:
                key = (cfg["user_id"], cfg["model"])
                daily_used = usage_map.get(key, 0)
                limit_today = cfg["max_tokens_per_day"]
                ratio = daily_used / limit_today if limit_today > 0 else 0
                if ratio >= cfg["alert_threshold"]:
                    alerts.append(
                        {
                            "user_id": cfg["user_id"],
                            "model": cfg["model"],
                            "daily_used": daily_used,
                            "daily_limit": limit_today,
                            "usage_ratio": round(ratio, 4),
                            "threshold": cfg["alert_threshold"],
                            "date": today,
                        }
                    )
        finally:
            conn.close()
        return alerts
