import json

from cloud.app.agent_runtime.models import AgentDecision

ALLOWED_ACTIONS = {"call_tool", "complete", "error"}


class AgentOutputValidator:
    @staticmethod
    def validate(reply: str | dict) -> tuple[AgentDecision | None, str | None]:
        try:
            data = json.loads(reply) if isinstance(reply, str) else reply
        except (json.JSONDecodeError, TypeError) as e:
            return None, f"failed to parse LLM response: {e}"

        action = data.get("action", "error")
        if action not in ALLOWED_ACTIONS:
            return None, f"invalid action: {action}, allowed: {sorted(ALLOWED_ACTIONS)}"

        decision = AgentDecision(
            action=action,
            tool=data.get("tool"),
            params=data.get("params"),
            reasoning=data.get("reasoning"),
        )
        return decision, None
