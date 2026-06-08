"""因果推理模块 — 线性模拟与反事实场景持久化。"""

import json
import uuid

from cloud.app.repositories import CounterfactualScenariosRepository


def _gen_scenario_id() -> str:
    return "cf:" + uuid.uuid4().hex[:8]


def _linear_simulate(scenario: dict) -> dict:
    """对单个反事实场景执行线性模拟计算。

    Args:
        scenario: 含 variable、from、to 的场景字典

    Returns:
        含变量、delta、预测结果和置信度的字典
    """
    variable = scenario.get("variable", "unknown")
    from_val = float(scenario.get("from", 0))
    to_val = float(scenario.get("to", 0))
    delta = to_val - from_val
    multiplier = 5.0
    change_pct = round(delta * multiplier, 1)
    outcome = {f"{variable}影响": f"{change_pct:+.1f}%"}
    conf = min(0.95, max(0.3, 0.55 + abs(delta) * 0.05))
    return {
        "variable": variable,
        "from": from_val,
        "to": to_val,
        "delta": delta,
        "predicted_outcome": outcome,
        "confidence": round(conf, 4),
    }


class CausalInferenceMixin:
    """反事实模拟与推理方法。"""

    def simulate_counterfactual(self, strategy_id: str, scenarios: list[dict], user_id: int) -> dict:
        """对给定策略执行反事实模拟并持久化结果。

        Args:
            strategy_id: 策略 ID
            scenarios: 场景列表，每项含 variable、from、to 字段
            user_id: 创建者用户 ID

        Returns:
            包含 simulations 列表和 total 计数的字典
        """
        cs_repo = CounterfactualScenariosRepository(self.db)
        results: list[dict] = []
        for sc in scenarios:
            sim = _linear_simulate(sc)
            scenario_id = _gen_scenario_id()
            cs_repo.create(
                {
                    "scenario_id": scenario_id,
                    "strategy_id": strategy_id,
                    "variable_changes": json.dumps(
                        [
                            {
                                "variable": sim["variable"],
                                "from": sim["from"],
                                "to": sim["to"],
                            }
                        ],
                        ensure_ascii=False,
                    ),
                    "predicted_outcome": json.dumps(sim["predicted_outcome"], ensure_ascii=False),
                    "confidence": sim["confidence"],
                    "created_by": user_id,
                }
            )
            results.append(
                {
                    "scenario_id": scenario_id,
                    "strategy_id": strategy_id,
                    "variable": sim["variable"],
                    "delta": sim["delta"],
                    "predicted_outcome": sim["predicted_outcome"],
                    "confidence": sim["confidence"],
                }
            )
        return {"simulations": results, "total": len(results)}
