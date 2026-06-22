"""EdacAgentTrigger — 从 AgentRepository 动态加载 Agent 的触发调度器。

唤醒词匹配：检查消息中是否包含 agent 的 name 或 agent_id。
Agent 信息完全来自 identity.yaml，无硬编码。"""

from __future__ import annotations

import logging
from pathlib import Path

from cloud.app.agent_runtime.core.models import AgentIdentity
from cloud.app.agents.agent_repository import AgentRepository

logger = logging.getLogger(__name__)

__all__ = ["EdacAgentTrigger"]


class EdacAgentTrigger:
    """基于 AgentRepository 动态加载 Agent 的触发调度器。"""

    def __init__(self, agents_dir: str | Path | None = None) -> None:
        self._agents_dir = agents_dir
        self._reload()

    def _reload(self) -> None:
        """从 AgentRepository 重新加载所有 Agent。"""
        self._agents: dict[str, AgentIdentity] = {}
        for model in AgentRepository.list_all(agents_dir=self._agents_dir):
            self._agents[model.key] = model

    def find_agent(self, message: str) -> AgentIdentity | None:
        """通过唤醒词匹配查找 Agent。匹配 agent_id 或 name（不区分大小写）。"""
        lower_msg = message.lower()
        for agent in self._agents.values():
            if agent.key.lower() in lower_msg or agent.name.lower() in lower_msg:
                return agent
        return None

    def get_agent(self, agent_id: str) -> AgentIdentity | None:
        """按 agent_id 获取 AgentIdentity。"""
        return self._agents.get(agent_id)

    def list_agents(self) -> list[AgentIdentity]:
        """返回所有已加载的 Agent 列表。"""
        return list(self._agents.values())

    @property
    def agent_ids(self) -> list[str]:
        return list(self._agents.keys())
