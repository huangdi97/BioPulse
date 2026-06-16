"""成本管控模块，按 token 用量估算并限制 LLM 调用成本。"""

import logging
import sqlite3

logger = logging.getLogger(__name__)


class CostGovernor:
    """LLM 调用成本控制器，累计 token 消耗并在超预算时阻止调用。"""

    MAX_COST_PER_TASK = 0.50
    PRICING = {
        "local": {"input_per_million": 0.0, "output_per_million": 0.0},
        "cloud_normal": {"input_per_million": 0.15, "output_per_million": 0.60},
        "cloud_agent": {"input_per_million": 0.45, "output_per_million": 1.80},
    }

    def __init__(self, max_cost: float = 0.50, model: str = "deepseek-chat"):
        self._max_cost = max_cost
        self._model = model
        self._total_cost = 0.0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._call_count = 0
        self._step_costs: list[dict] = []

    @staticmethod
    def estimate_cost(tokens_input: int, tokens_output: int, model_tier: str) -> float:
        """估算 LLM 调用成本。"""
        pricing = CostGovernor.PRICING.get(model_tier, CostGovernor.PRICING["cloud_normal"])
        return (tokens_input * pricing["input_per_million"] + tokens_output * pricing["output_per_million"]) / 1e6

    def check(self, model: str, input_tokens: int, output_tokens: int, model_tier: str = "cloud_normal") -> bool:
        """检查当前调用是否在预算范围内。"""
        estimated_cost = self.estimate_cost(input_tokens, output_tokens, model_tier)
        return (self._total_cost + estimated_cost) <= self._max_cost

    def record(self, model: str, input_tokens: int, output_tokens: int, model_tier: str = "cloud_normal", step: int | None = None) -> float:
        """记录一次 LLM 调用的 token 消耗与成本。"""
        cost = self.estimate_cost(input_tokens, output_tokens, model_tier)
        self._total_cost += cost
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        self._call_count += 1
        self._step_costs.append(
            {
                "step": step,
                "model": model,
                "model_tier": model_tier,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": round(cost, 9),
            }
        )
        return cost

    def record_step_cost(self, cost_data: dict, step: int | None = None) -> float:
        """记录步骤级成本数据。"""
        input_tokens = int(cost_data.get("input_tokens", 0))
        output_tokens = int(cost_data.get("output_tokens", 0))
        model_tier = cost_data.get("model_tier", "cloud_normal")
        model = cost_data.get("model", self._model)
        if "cost" in cost_data:
            cost = float(cost_data.get("cost", 0.0))
            self._total_cost += cost
            self._total_input_tokens += input_tokens
            self._total_output_tokens += output_tokens
            self._call_count += 1
            self._step_costs.append(
                {
                    "step": step,
                    "model": model,
                    "model_tier": model_tier,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": round(cost, 9),
                }
            )
            return cost
        return self.record(model, input_tokens, output_tokens, model_tier, step)

    def is_over_budget(self) -> bool:
        """检查是否已超出预算。"""
        over = self._total_cost > self._max_cost
        if over:
            logger.warning("CostGovernor: budget exceeded, total_cost=%.4f, max_cost=%.4f", self._total_cost, self._max_cost)
        return over

    def reset(self):
        """重置成本跟踪数据。"""
        self._total_cost = 0.0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._call_count = 0
        self._step_costs = []

    def restore_usage(self, usage: dict | None) -> None:
        """从外部数据恢复成本使用状态。"""
        usage = usage or {}
        self._total_cost = float(usage.get("total_cost", 0.0) or 0.0)
        self._total_input_tokens = int(usage.get("total_input_tokens", 0) or 0)
        self._total_output_tokens = int(usage.get("total_output_tokens", 0) or 0)
        self._call_count = int(usage.get("call_count", 0) or 0)
        self._step_costs = list(usage.get("step_costs", []) or [])

    def record_call(self, agent_name: str, model: str, input_tokens: int, output_tokens: int, cost: float, trace_id: str = "", db=None):
        """记录一次 LLM 调用到数据库。"""
        if db is None:
            return
        try:
            db.execute(
                "INSERT INTO agent_cost_tracking (agent_name, model, model_tier, input_tokens, output_tokens, cost, trace_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (agent_name, model, model, input_tokens, output_tokens, round(cost, 9), trace_id),
            )
            db.commit()
        except sqlite3.Error:
            logger.exception("Failed to record cost tracking entry")

    def get_daily_costs(self, db, start: str, end: str) -> list[dict]:
        """获取每日成本汇总。"""
        rows = db.execute(
            "SELECT DATE(timestamp) as day, SUM(cost) as total_cost, SUM(input_tokens) as total_input, "
            "SUM(output_tokens) as total_output, COUNT(*) as call_count "
            "FROM agent_cost_tracking WHERE DATE(timestamp) >= ? AND DATE(timestamp) <= ? "
            "GROUP BY DATE(timestamp) ORDER BY day",
            (start, end),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_costs_by_agent(self, db) -> list[dict]:
        """获取各 Agent 的成本统计。"""
        rows = db.execute(
            "SELECT agent_name, SUM(cost) as total_cost, SUM(input_tokens) as total_input, "
            "SUM(output_tokens) as total_output, COUNT(*) as call_count "
            "FROM agent_cost_tracking GROUP BY agent_name ORDER BY total_cost DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_costs_by_model(self, db) -> list[dict]:
        """获取各模型的成本统计。"""
        rows = db.execute(
            "SELECT model, SUM(cost) as total_cost, SUM(input_tokens) as total_input, "
            "SUM(output_tokens) as total_output, COUNT(*) as call_count "
            "FROM agent_cost_tracking GROUP BY model ORDER BY total_cost DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_usage(self) -> dict:
        """获取当前成本使用详情。"""
        step_cost = self._step_costs[-1]["cost"] if self._step_costs else 0.0
        return {
            "model": self._model,
            "total_cost": round(self._total_cost, 6),
            "step_cost": step_cost,
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
            "call_count": self._call_count,
            "max_cost": self._max_cost,
            "step_costs": list(self._step_costs),
        }
