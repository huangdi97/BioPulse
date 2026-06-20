"""执行失败时的 failover 逻辑 — 自动转移至备用 Agent 或进入死信队列。"""

import logging
import time

from cloud.app.agent_runtime.agent_registry import AgentRegistry
from cloud.app.agent_runtime.dead_letter_queue import DeadLetterQueue
from cloud.app.agent_runtime.models import RuntimeResult
from cloud.app.agent_runtime.pii_redactor import PIIRedactionFilter

logger = logging.getLogger(__name__)
logger.addFilter(PIIRedactionFilter())


class FailoverHandler:
    def __init__(self, host):
        self._host = host
        self._dead_letter_queue = DeadLetterQueue()

    def handle_failover(self, agent_key: str, goal: str, context: dict | None, exc: Exception, error_type: str) -> tuple[RuntimeResult | None, bool]:
        """尝试 failover 到备用 agent；返回 (result, handled)，handled=True 表示已转移。"""
        failover = AgentRegistry.find_failover_agent(agent_key)
        if failover:
            logger.info("Failover from %s to %s (%s)", agent_key, failover, error_type)
            return self._host.execute(goal, failover, context), True
        self._dead_letter_queue.push(
            {
                "agent_key": agent_key,
                "input": goal,
                "error": f"{error_type}: {exc}",
                "timestamp": time.time(),
                "retry_count": 0,
            }
        )
        return None, False
