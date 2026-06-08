"""Token budget management service.

Provides budget configuration, usage tracking, quota checking,
and usage reporting for LLM token consumption per user per model.
"""

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from cloud.app.database import DB_PATH
from cloud.app.services.token_estimator import TokenEstimatorMixin

_RULES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "rules",
)
_RULES_PATH = os.path.join(_RULES_DIR, "token_budget_rules.json")


@dataclass
class TokenBudgetConfig:
    model: str
    max_tokens_per_day: int
    max_tokens_per_request: int
    alert_threshold: float
    user_id: int


def _load_rules() -> dict:
    """从规则 JSON 文件中加载 token 预算规则配置。

    Returns:
        规则字典，含 default_alert_threshold, models, overrides。
    """
    if not os.path.exists(_RULES_PATH):
        return {"default_alert_threshold": 0.8, "models": {}, "overrides": {}}
    with open(_RULES_PATH, encoding="utf-8") as f:
        return json.load(f)


def _connect():
    """创建并返回一个 SQLite 数据库连接，使用字典行工厂。

    Returns:
        sqlite3.Connection 对象。
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class TokenBudgetService(TokenEstimatorMixin):
    PRICING = {
        "deepseek-chat": {"input_per_million": 0.14, "output_per_million": 0.28},
        "deepseek-v4-pro": {"input_per_million": 0.14, "output_per_million": 0.28},
    }

    def __init__(self):
        """初始化 TokenBudgetService，加载规则配置。"""
        self._rules = _load_rules()

    @classmethod
    def get_pricing(cls, model: str) -> dict:
        """Return the pricing configuration for a given model.

        Args:
            model: The model name (e.g. "deepseek-chat").

        Returns:
            A dict with input_per_million and output_per_million cost values.
        """
        return cls.PRICING.get(model, {"input_per_million": 0.14, "output_per_million": 0.28})

    def _get_model_config(self, model: str) -> dict:
        """获取指定模型的全局 token 预算配置。

        Args:
            model: 模型名称。

        Returns:
            含 max_tokens_per_day 和 max_tokens_per_request 的配置字典。
        """
        models = self._rules.get("models", {})
        config = models.get(model, {})
        if not config:
            config = {
                "max_tokens_per_day": 100000,
                "max_tokens_per_request": 16000,
            }
        return config

    def _get_override(self, user_id: int, model: str) -> Optional[dict]:
        """获取指定用户和模型的自定义预算覆盖配置。

        Args:
            user_id: 用户 ID。
            model: 模型名称。

        Returns:
            覆盖配置字典，若未配置则返回 None。
        """
        overrides = self._rules.get("overrides", {})
        user_overrides = overrides.get(str(user_id), {})
        return user_overrides.get(model)

    def get_budget(self, user_id: int, model: str) -> dict:
        """Retrieve the token budget configuration for a user and model.

        Merges the model-wide defaults with any user-specific overrides.

        Args:
            user_id: The user's ID.
            model: The model name.

        Returns:
            A dict with user_id, model, max_tokens_per_day, max_tokens_per_request, and alert_threshold.
        """
        model_config = self._get_model_config(model)
        override = self._get_override(user_id, model)
        alert_threshold = self._rules.get("default_alert_threshold", 0.8)
        if override:
            model_config.update(override)
            if "alert_threshold" in override:
                alert_threshold = override["alert_threshold"]
        return {
            "user_id": user_id,
            "model": model,
            "max_tokens_per_day": model_config.get("max_tokens_per_day", 100000),
            "max_tokens_per_request": model_config.get("max_tokens_per_request", 16000),
            "alert_threshold": alert_threshold,
        }

    def record_usage(self, user_id: int, model: str, tokens: int, cost: float) -> dict:
        """Record actual token usage and update the daily budget tracking table.

        Args:
            user_id: The user's ID.
            model: The model name.
            tokens: The number of tokens consumed.
            cost: The cost incurred for this usage.

        Returns:
            A dict containing the recorded usage details (user_id, model, tokens, cost, usage_date).
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
        """Generate a token usage report for a user over a specified number of days.

        Args:
            user_id: The user's ID.
            days: Number of days to look back (default 30).

        Returns:
            A list of dicts grouped by usage_date and model, each with total_tokens, total_cost, and call_count.
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

    def list_alert_configs(self) -> list:
        """List current budget configurations for all users and models.

        Returns:
            A list of dicts, each representing a user-model budget configuration.
        """
        conn = _connect()
        try:
            rows = conn.execute("SELECT DISTINCT user_id, model FROM token_budget ORDER BY user_id, model").fetchall()
        finally:
            conn.close()
        results = []
        for row in rows:
            results.append(self.get_budget(row["user_id"], row["model"]))
        return results

    def update_budget(
        self,
        user_id: int,
        model: str,
        max_tokens_per_day: Optional[int] = None,
        max_tokens_per_request: Optional[int] = None,
        alert_threshold: Optional[float] = None,
    ) -> dict:
        """Update token budget overrides for a specific user and model.

        Only provided fields are updated; others retain existing values.
        The overrides are persisted to the rules JSON file.

        Args:
            user_id: The user's ID.
            model: The model name.
            max_tokens_per_day: Optional new daily token limit.
            max_tokens_per_request: Optional new per-request token limit.
            alert_threshold: Optional new alert threshold (0.0 to 1.0).

        Returns:
            A dict representing the updated budget configuration.
        """
        override_key = str(user_id)
        overrides = self._rules.setdefault("overrides", {})
        user_override = overrides.setdefault(override_key, {})
        model_override = user_override.setdefault(model, {})
        if max_tokens_per_day is not None:
            model_override["max_tokens_per_day"] = max_tokens_per_day
        if max_tokens_per_request is not None:
            model_override["max_tokens_per_request"] = max_tokens_per_request
        if alert_threshold is not None:
            model_override["alert_threshold"] = alert_threshold
        os.makedirs(os.path.dirname(_RULES_PATH), exist_ok=True)
        with open(_RULES_PATH, "w", encoding="utf-8") as f:
            json.dump(self._rules, f, ensure_ascii=False, indent=2)
        return self.get_budget(user_id, model)

    def get_alerts(self) -> list:
        """Retrieve alerts for all users whose usage ratio meets or exceeds their alert threshold.

        Returns:
            A list of alert dicts with user_id, model, daily_used, daily_limit, usage_ratio, threshold, and date.
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        configs = self.list_alert_configs()
        alerts = []
        conn = _connect()
        try:
            for cfg in configs:
                row = conn.execute(
                    "SELECT COALESCE(SUM(tokens), 0) AS total FROM token_usage WHERE user_id=? AND model=? AND usage_date=?",
                    (cfg["user_id"], cfg["model"], today),
                ).fetchone()
                daily_used = row["total"] if row else 0
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
