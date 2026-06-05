from cloud.app.services.token_budget_service import TokenBudgetService


class CostGovernor:
    def __init__(self, max_cost: float = 0.50, model: str = "deepseek-chat"):
        self._max_cost = max_cost
        self._model = model
        self._total_cost = 0.0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._call_count = 0
        pricing = TokenBudgetService.get_pricing(model)
        self._price_input = pricing["input_per_million"] / 1e6
        self._price_output = pricing["output_per_million"] / 1e6

    def check(self, model: str, input_tokens: int, output_tokens: int) -> bool:
        estimated_cost = input_tokens * self._price_input + output_tokens * self._price_output
        return (self._total_cost + estimated_cost) <= self._max_cost

    def record(self, model: str, input_tokens: int, output_tokens: int) -> float:
        cost = input_tokens * self._price_input + output_tokens * self._price_output
        self._total_cost += cost
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        self._call_count += 1
        return cost

    def reset(self):
        self._total_cost = 0.0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._call_count = 0

    def get_usage(self) -> dict:
        return {
            "model": self._model,
            "total_cost": round(self._total_cost, 6),
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
            "call_count": self._call_count,
            "max_cost": self._max_cost,
        }
