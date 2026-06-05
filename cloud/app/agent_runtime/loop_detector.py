from cloud.app.agent_runtime.models import AgentDecision


class LoopDetector:
    def __init__(self) -> None:
        self.history: list[AgentDecision] = []

    def record(self, decision: AgentDecision) -> None:
        self.history.append(decision)

    def detect(self) -> str | None:
        if len(self.history) < 3:
            return None
        recent = self.history[-3:]
        names = [d.tool for d in recent]
        params = [str(d.params) for d in recent]
        if len(set(names)) == 1 and all(p == params[0] for p in params):
            return f"Loop detected: tool '{names[0]}' called 3 times with identical params"
        return None

    def reset(self) -> None:
        self.history.clear()
