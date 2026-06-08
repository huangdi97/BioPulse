"""Token 预算估算与校验方法。"""

import sqlite3
from datetime import datetime, timezone

from cloud.app.database import DB_PATH


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class TokenEstimatorMixin:
    """Token 使用估算和预算校验方法。"""

    def check_budget(self, user_id: int, model: str, estimated_tokens: int) -> dict:
        """Check whether an estimated token usage would exceed the user's budget limits.

        Verifies both the per-request limit and the cumulative daily limit.

        Args:
            user_id: The user's ID.
            model: The model name.
            estimated_tokens: The estimated number of tokens for the upcoming request.

        Returns:
            A dict with allowed (bool), reason (str), daily_used (int), and daily_limit (int).
        """
        budget = self.get_budget(user_id, model)
        daily_limit = budget["max_tokens_per_day"]
        request_limit = budget["max_tokens_per_request"]
        alert_threshold = budget["alert_threshold"]
        if estimated_tokens > request_limit:
            return {
                "allowed": False,
                "reason": f"请求 tokens {estimated_tokens} 超过单次上限 {request_limit}",
                "daily_used": 0,
                "daily_limit": daily_limit,
            }
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT COALESCE(SUM(tokens), 0) AS total FROM token_usage WHERE user_id=? AND model=? AND usage_date=?",
                (user_id, model, today),
            ).fetchone()
            daily_used = row["total"] if row else 0
        finally:
            conn.close()
        if daily_used + estimated_tokens > daily_limit:
            return {
                "allowed": False,
                "reason": f"每日配额不足：已用 {daily_used} / {daily_limit}，需 {estimated_tokens}",
                "daily_used": daily_used,
                "daily_limit": daily_limit,
            }
        usage_ratio = (daily_used + estimated_tokens) / daily_limit if daily_limit > 0 else 0
        nearing_limit = usage_ratio >= alert_threshold
        return {
            "allowed": True,
            "reason": "ok" if not nearing_limit else f"用量已达 {usage_ratio:.0%}，接近告警阈值 {alert_threshold:.0%}",
            "daily_used": daily_used,
            "daily_limit": daily_limit,
        }
