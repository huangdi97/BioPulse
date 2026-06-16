"""Agent 数据模型 — 从 identity.yaml 结构映射的不可变 dataclass。"""

from __future__ import annotations

from dataclasses import dataclass, field

from cloud.app.agents.safety_profile import AgentSafetyProfile

__all__ = ["AgentModel"]


@dataclass(frozen=True)
class AgentModel:
    """Agent 身份模型，对应 agents/*/identity.yaml 的核心字段。"""

    agent_id: str
    name: str
    persona: str
    capabilities: list[str] = field(default_factory=list)
    model_preference: str = ""
    safety_level: str = "read"
    interrupt_behavior: str = "user_request"
    safety_profile: AgentSafetyProfile = field(default_factory=lambda: AgentSafetyProfile.from_safety_level("read"))
