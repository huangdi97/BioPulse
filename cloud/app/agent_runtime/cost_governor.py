"""成本管控模块，按 token 用量估算并限制 LLM 调用成本。"""


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
        pricing = CostGovernor.PRICING.get(model_tier, CostGovernor.PRICING["cloud_normal"])
        return (tokens_input * pricing["input_per_million"] + tokens_output * pricing["output_per_million"]) / 1e6

    def check(self, model: str, input_tokens: int, output_tokens: int, model_tier: str = "cloud_normal") -> bool:
        estimated_cost = self.estimate_cost(input_tokens, output_tokens, model_tier)
        return (self._total_cost + estimated_cost) <= self._max_cost

    def record(self, model: str, input_tokens: int, output_tokens: int, model_tier: str = "cloud_normal", step: int | None = None) -> float:
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
        return self._total_cost > self._max_cost

    def reset(self):
        self._total_cost = 0.0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._call_count = 0
        self._step_costs = []

    def restore_usage(self, usage: dict | None) -> None:
        usage = usage or {}
        self._total_cost = float(usage.get("total_cost", 0.0) or 0.0)
        self._total_input_tokens = int(usage.get("total_input_tokens", 0) or 0)
        self._total_output_tokens = int(usage.get("total_output_tokens", 0) or 0)
        self._call_count = int(usage.get("call_count", 0) or 0)
        self._step_costs = list(usage.get("step_costs", []) or [])

    def get_usage(self) -> dict:
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
