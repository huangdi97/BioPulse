"""SpecializedAgent — 调用 LLM + Memory + ToolBridge 的 Agent 默认实现。"""

from __future__ import annotations

import logging
from typing import Any

from cloud.app.agents.agent_model import AgentModel
from cloud.app.agents.base_agent import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)

__all__ = ["SpecializedAgent"]


class SpecializedAgent(BaseAgent):
    """调用 llm_service + memory_service + tool_bridge 的 Agent 实现。"""

    def __init__(
        self,
        agent_model: AgentModel,
        llm_service: Any = None,
        memory_service: Any = None,
        tool_bridge: Any = None,
    ) -> None:
        self._model = agent_model
        self._llm = llm_service
        self._memory = memory_service
        self._tools = tool_bridge

    @classmethod
    def from_model(
        cls,
        agent_model: AgentModel,
        services: dict[str, Any] | None = None,
    ) -> SpecializedAgent:
        """工厂方法，从 AgentModel 和服务字典构造实例。"""
        services = services or {}
        return cls(
            agent_model=agent_model,
            llm_service=services.get("llm_service"),
            memory_service=services.get("memory_service"),
            tool_bridge=services.get("tool_bridge"),
        )

    async def execute(self, context: AgentContext) -> AgentResponse:
        """执行 Agent 逻辑，调用 LLM 生成回复，使用工具和记忆。"""
        logger.info(
            "SpecializedAgent(%s) execute: %s",
            self._model.agent_id,
            context.message[:64],
        )
        namespace = None
        if self._memory is not None:
            try:
                namespace = self._memory.get_namespace(self._model.agent_id)
            except Exception:
                logger.exception("Failed to get memory namespace for %s", self._model.agent_id)
        prompt = self._build_prompt(context, namespace=namespace)
        reply = ""
        if self._llm is not None:
            try:
                reply = await self._llm.generate(prompt)
            except Exception:
                logger.exception("LLM call failed for agent %s", self._model.agent_id)
                reply = f"[{self._model.name}] 处理出错，请稍后重试。"
        else:
            reply = f"[{self._model.name}] 已收到: {context.message}"
        return AgentResponse(reply=reply, actions=[], memory_updates=[])

    def capabilities(self) -> list[str]:
        """返回从 identity.yaml 加载的能力列表。"""
        return list(self._model.capabilities)

    def _build_prompt(self, context: AgentContext, namespace: object = None) -> str:
        """构造发送给 LLM 的 prompt。"""
        parts = [
            f"你是一个 {self._model.name}，负责: {self._model.persona}",
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
