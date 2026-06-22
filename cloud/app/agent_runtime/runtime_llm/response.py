"""LLM response parsing and annotation."""

from cloud.app.agent_runtime.safety.cost_governor import CostGovernor


def usage_from_route_result(result: dict) -> dict:
    """usage from route result."""
    if not result.get("success"):
        return {}
    data = result.get("data") or {}
    if "data" in data:
        return data.get("data", {}).get("usage", {}) or {}
    return data.get("usage", {}) or {}


def annotate_route_result(result: dict, model_tier: str) -> dict:
    """annotate route result."""
    tier = result.get("model_tier", model_tier)
    usage = usage_from_route_result(result)
    input_tokens = int(usage.get("prompt_tokens", 0) or 0)
    output_tokens = int(usage.get("completion_tokens", 0) or 0)
    result["model_tier"] = tier
    result["cost"] = {
        "model_tier": tier,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": round(CostGovernor.estimate_cost(input_tokens, output_tokens, tier), 9),
    }
    return result
