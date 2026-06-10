"""因果推断收集来源。"""

from __future__ import annotations

import sqlite3
from typing import Any


class CausalInferenceRunner:
    """为 CausalInferenceMixin 提供 db 属性的轻量运行器。"""

    def __init__(self, db: sqlite3.Connection) -> None:
        """初始化因果推断运行器。

        Args:
            db: SQLite 数据库连接。

        Returns:
            None。
        """
        self.db = db

    def simulate_counterfactual(self, strategy_id: str, scenarios: list[dict[str, Any]], user_id: int) -> dict[str, Any]:
        """调用 causal_inference.py 的反事实模拟实现。

        Args:
            strategy_id: 策略 ID。
            scenarios: 反事实场景列表。
            user_id: 用户 ID。

        Returns:
            因果推断模拟结果。
        """
        from ..services.causal_inference import CausalInferenceMixin

        return CausalInferenceMixin.simulate_counterfactual(self, strategy_id, scenarios, user_id)


def run_causal_attribution(db: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    """调用 causal_inference.py 中的反事实推断能力。

    Args:
        db: 数据库连接。
        args: 包含 strategy_id、rep_id 与 hcp_id 的参数。

    Returns:
        因果推断结果；缺少持久化表时返回可解释降级结果。
    """
    scenarios = [
        {"variable": "visit_frequency", "from": 1, "to": 3},
        {"variable": "academic_support", "from": 0, "to": 1},
        {"variable": "competitor_pressure", "from": 2, "to": 1},
    ]
    try:
        return CausalInferenceRunner(db).simulate_counterfactual(
            str(args.get("strategy_id", "sales_suggestion")),
            scenarios,
            int(args.get("rep_id") or 0),
        )
    except Exception as exc:
        return {
            "simulations": [fallback_simulation(sc) for sc in scenarios],
            "total": len(scenarios),
            "persistence": "skipped",
            "reason": str(exc),
        }


def fallback_simulation(scenario: dict[str, Any]) -> dict[str, Any]:
    """生成不依赖数据库持久化的反事实模拟结果。

    Args:
        scenario: 反事实变量变更。

    Returns:
        单个模拟结果。
    """
    from_value = float(scenario.get("from", 0))
    to_value = float(scenario.get("to", 0))
    delta = to_value - from_value
    return {
        "variable": scenario.get("variable", "unknown"),
        "delta": delta,
        "predicted_outcome": {"strategy_effect": f"{delta * 5:+.1f}%"},
        "confidence": round(min(0.9, max(0.35, 0.55 + abs(delta) * 0.05)), 4),
    }
