"""L0 隔离防线 — Agent 间传染病防御。

每个 Agent 的 context 完全隔离，禁止直接输出作为另一个 Agent 的 system prompt。
只允许通过 SharedState（schema 校验）或 StructuredHandoff（类型校验）传递信息。
"""

import logging
import time

from cloud.app.agent_runtime.core.shared_state import SharedStateEntry, get_shared_state

logger = logging.getLogger(__name__)

_quarantined_agents: dict[str, float] = {}


class DefensePipelineL0:
    def __init__(self):
        self._ss = get_shared_state()

    def check_isolation(self, source_agent: str, target_agent: str, content: str, context: dict | None = None) -> bool:
        if source_agent in _quarantined_agents:
            logger.warning("Blocked communication from quarantined agent: %s", source_agent)
            return False
        if target_agent in _quarantined_agents:
            logger.warning("Blocked communication to quarantined agent: %s", target_agent)
            return False
        if context and "system_prompt" in context:
            logger.warning("L0 block: agent %s tried to inject system prompt into agent %s", source_agent, target_agent)
            return False
        return True

    def validate_handoff(self, source_agent: str, target_agent: str, artifact_type: str) -> bool:
        allowed_artifact_types = {"compliance_report", "visit_plan", "competitor_brief", "expense_audit", "insight_card"}
        if artifact_type not in allowed_artifact_types:
            logger.warning("L0 block: unknown artifact type '%s' from %s to %s", artifact_type, source_agent, target_agent)
            return False
        return True

    def validate_shared_state_write(self, entry: SharedStateEntry, caller_agent_key: str) -> bool:
        if caller_agent_key in _quarantined_agents:
            logger.warning("L0 block: quarantined agent %s tried to write SharedState", caller_agent_key)
            return False
        return True


def quarantine(agent_key: str) -> None:
    _quarantined_agents[agent_key] = time.time()
    logger.warning("Agent %s has been QUARANTINED at %.0f", agent_key, time.time())


def unquarantine(agent_key: str) -> bool:
    if agent_key in _quarantined_agents:
        del _quarantined_agents[agent_key]
        logger.info("Agent %s has been released from quarantine", agent_key)
        return True
    return False


def is_quarantined(agent_key: str) -> bool:
    return agent_key in _quarantined_agents


def list_quarantined() -> dict[str, float]:
    return dict(_quarantined_agents)
