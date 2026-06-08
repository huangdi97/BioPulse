"""Token budget management service.

Provides budget configuration, usage tracking, quota checking,
and usage reporting for LLM token consumption per user per model.
"""

import json
import os
from dataclasses import dataclass
from typing import Optional

from cloud.app.services.budget_tracker import BudgetTracker
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
    if not os.path.exists(_RULES_PATH):
        return {"default_alert_threshold": 0.8, "models": {}, "overrides": {}}
    with open(_RULES_PATH, encoding="utf-8") as f:
        return json.load(f)


class TokenBudgetService(TokenEstimatorMixin, BudgetTracker):
    PRICING = {
        "deepseek-chat": {"input_per_million": 0.14, "output_per_million": 0.28},
        "deepseek-v4-pro": {"input_per_million": 0.14, "output_per_million": 0.28},
    }

    def __init__(self):
        self._rules = _load_rules()

    @classmethod
    def get_pricing(cls, model: str) -> dict:
        """返回指定模型的Token计价配置。

        Args:
            model: 模型名称。

        Returns:
            包含每百万输入和输出Token价格的字典。

        Raises:
            KeyError: 不会主动抛出；未知模型返回默认价格。
        """
        return cls.PRICING.get(model, {"input_per_million": 0.14, "output_per_million": 0.28})

    def _get_model_config(self, model: str) -> dict:
        models = self._rules.get("models", {})
        config = models.get(model, {})
        if not config:
            config = {
                "max_tokens_per_day": 100000,
                "max_tokens_per_request": 16000,
            }
        return config

    def _get_override(self, user_id: int, model: str) -> Optional[dict]:
        overrides = self._rules.get("overrides", {})
        user_overrides = overrides.get(str(user_id), {})
        return user_overrides.get(model)

    def get_budget(self, user_id: int, model: str) -> dict:
        """读取用户在指定模型上的预算配置。

        Args:
            user_id: 用户ID。
            model: 模型名称。

        Returns:
            包含日限额、单请求限额和告警阈值的预算字典。

        Raises:
            OSError: 当规则文件读取异常时由初始化流程抛出。
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

    def list_alert_configs(self) -> list:
        """列出已有用量记录对应的告警配置。

        Args:
            None.

        Returns:
            用户和模型维度的预算配置列表。

        Raises:
            sqlite3.Error: 当token budget数据库查询失败时抛出。
        """
        from cloud.app.services.budget_tracker import _connect

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
        """更新用户指定模型的预算覆盖配置。

        Args:
            user_id: 用户ID。
            model: 模型名称。
            max_tokens_per_day: 可选的新每日Token上限。
            max_tokens_per_request: 可选的新单请求Token上限。
            alert_threshold: 可选的新告警阈值。

        Returns:
            更新后的预算配置字典。

        Raises:
            OSError: 当规则目录创建或规则文件写入失败时抛出。
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
        """计算当前触发阈值的Token预算告警。

        Args:
            None.

        Returns:
            达到告警阈值的用户模型用量列表。

        Raises:
            sqlite3.Error: 当用量或预算查询失败时由底层追踪器抛出。
        """
        configs = self.list_alert_configs()
        return super().get_alerts(configs)
