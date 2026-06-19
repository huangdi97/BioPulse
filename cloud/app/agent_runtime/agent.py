"""Agent 实体 — 从 identity.yaml 加载并持有运行时组件引用。"""

import logging
import os
from pathlib import Path

import yaml

from cloud.app.agent_runtime.cost_governor import CostGovernor
from cloud.app.agent_runtime.memory import Memory
from cloud.app.agent_runtime.model_router import ModelRouter
from cloud.app.agent_runtime.models import AgentIdentity, Insight
from cloud.app.agent_runtime.safety_guard import SafetyGuard
from cloud.app.agent_runtime.tool_bridge import ToolBridge

logger = logging.getLogger(__name__)


class Agent:
    def __init__(self, identity: AgentIdentity, db=None):
        self.identity = identity
        self.tools = ToolBridge()
        self.memory = Memory(db)
        self.cost_governor = CostGovernor(max_cost=identity.cost_budget)
        self.safety = SafetyGuard()
        self.model_router = ModelRouter(identity.model_preference)

    @classmethod
    def from_yaml(cls, path: str | os.PathLike) -> "Agent":
        path = Path(path)
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        identity = AgentIdentity(**data)
        return cls(identity)

    async def insights_for(self, page_id: str, user_id: str) -> list[Insight]:
        """insights for."""
        return [
            Insight(
                agent_key=self.identity.key,
                page_id=page_id,
                summary=f"{self.identity.name} 就绪",
                details={
                    "role": self.identity.role,
                    "goal": self.identity.goal,
                    "memory_namespace": self.identity.memory_namespace,
                },
                confidence=1.0,
            )
        ]
