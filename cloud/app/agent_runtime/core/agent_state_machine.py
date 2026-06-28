import logging

from cloud.app.agent_runtime.core.shared_state import SharedStateEntry, get_shared_state

logger = logging.getLogger(__name__)

_TRANSITIONS = {
    "IDLE": {"PERCEIVING", "ERROR"},
    "PERCEIVING": {"PLANNING", "ERROR"},
    "PLANNING": {"EXECUTING", "ERROR"},
    "EXECUTING": {"REFLECTING", "ERROR"},
    "REFLECTING": {"PLANNING", "IDLE", "ERROR"},
    "ERROR": {"RECOVERING", "ERROR"},
    "RECOVERING": {"IDLE", "ERROR"},
}

_STATES = frozenset(_TRANSITIONS.keys())


class AgentStateMachine:
    def __init__(self):
        self._state = "IDLE"

    @property
    def state(self) -> str:
        return self._state

    def transition(self, target: str, agent_key: str = "", **kwargs) -> None:
        if target not in _STATES:
            raise ValueError(f"Unknown state: {target}")
        if target not in _TRANSITIONS.get(self._state, set()):
            raise ValueError(f"Invalid transition from {self._state} to {target}")

        old_state = self._state
        self._state = target

        ss = get_shared_state()
        entry = SharedStateEntry(
            namespace=f"agent.{agent_key}",
            key="state",
            value=target,
            agent_key=agent_key,
        )
        ss.write(entry)

        logger.debug("Agent %s state: %s -> %s", agent_key, old_state, target)

    def reset(self, agent_key: str = "") -> None:
        self._state = "IDLE"
        ss = get_shared_state()
        entry = SharedStateEntry(
            namespace=f"agent.{agent_key}",
            key="state",
            value="IDLE",
            agent_key=agent_key,
        )
        ss.write(entry)
