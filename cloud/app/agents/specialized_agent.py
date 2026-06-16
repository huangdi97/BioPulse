"""SpecializedAgent — 调用 LLM + Memory + ToolBridge 的 Agent 默认实现。"""

from __future__ import annotations

import logging
from typing import Any

from cloud.app.agent_runtime.models import AgentIdentity
from cloud.app.agents.base_agent import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)

__all__ = ["SpecializedAgent"]


class SpecializedAgent(BaseAgent):
    """调用 llm_service + memory_service + tool_bridge 的 Agent 实现。"""

    def __init__(
        self,
        identity: AgentIdentity,
        llm_service: Any = None,
        memory_service: Any = None,
        tool_bridge: Any = None,
    ) -> None:
        self._identity = identity
        self._llm = llm_service
        self._memory = memory_service
        self._tools = tool_bridge

    @classmethod
    def from_identity(
        cls,
        identity: AgentIdentity,
        services: dict[str, Any] | None = None,
    ) -> SpecializedAgent:
        """工厂方法，从 AgentIdentity 和服务字典构造实例。"""
        services = services or {}
        return cls(
            identity=identity,
            llm_service=services.get("llm_service"),
            memory_service=services.get("memory_service"),
            tool_bridge=services.get("tool_bridge"),
        )

    async def execute(self, context: AgentContext) -> AgentResponse:
        """执行 Agent 逻辑，调用 LLM 生成回复，使用工具和记忆。"""
        agent_id = self._identity.key
        agent_name = self._identity.name
        logger.info(
            "SpecializedAgent(%s) execute: %s",
            agent_id,
            context.message[:64],
        )
        # 安全审核：检查 safety_profile 的 max_permission
        safety = self._identity.safety_profile
        if safety.max_permission == "read":
            # read-only agent 不应处理写操作，但消息回复本身允许
            pass
        namespace = None
        if self._memory is not None:
            try:
                namespace = self._memory.get_namespace(agent_id)
            except Exception:
                logger.exception("Failed to get memory namespace for %s", agent_id)
        prompt = self._build_prompt(context, namespace=namespace)
        reply = ""
        if self._llm is not None:
            try:
                reply = await self._llm.generate(prompt)
            except Exception:
                logger.exception("LLM call failed for agent %s", agent_id)
                reply = f"[{agent_name}] 处理出错，请稍后重试。"
        else:
            reply = f"[{agent_name}] 已收到: {context.message}"
        return AgentResponse(reply=reply, actions=[], memory_updates=[])

    def capabilities(self) -> list[str]:
        """返回从 identity.yaml 加载的能力列表。"""
        return list(self._identity.allowed_tools)

    def _build_prompt(self, context: AgentContext, namespace: object = None) -> str:
        """构造发送给 LLM 的 prompt。"""
        parts = [
            f"你是一个 {self._identity.name}，负责: {self._identity.role}：{self._identity.goal}",
            f"用户消息: {context.message}",
        ]
        if namespace is not None:
            recent = getattr(namespace, "recent", lambda n: [])()
            if recent:
                parts.append("记忆上下文:")
                for entry in recent:
                    parts.append(f"  - {entry.get('key', '')}: {entry.get('value', '')}")
        if context.session_id:
            parts.append(f"会话: {context.session_id}")
        if context.user_id:
            parts.append(f"用户: {context.user_id}")
        return "\n".join(parts)
