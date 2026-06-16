"""Agent 核心模块 — 仓库、抽象基类与具体实现。"""

from cloud.app.agent_runtime.models import AgentIdentity
from cloud.app.agents.agent_repository import AgentRepository
from cloud.app.agents.base_agent import AgentContext, AgentResponse, BaseAgent
from cloud.app.agents.edac_agent_trigger import EdacAgentTrigger
from cloud.app.agents.model_router import ModelRouter, RouteResult
from cloud.app.agents.specialized_agent import SpecializedAgent

__all__ = [
    "AgentRepository",
    "AgentContext",
    "AgentResponse",
    "BaseAgent",
    "EdacAgentTrigger",
    "ModelRouter",
    "RouteResult",
    "SpecializedAgent",
    "AgentIdentity",
]
