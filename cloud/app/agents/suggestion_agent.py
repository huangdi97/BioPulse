"""SuggestionAgent — 销售策略建议 Agent，为 sales_suggestion 提供专用执行逻辑。

集成 HCP 画像、拜访历史、竞品情报，通过 LLM 生成结构化销售策略建议。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from cloud.app.agent_runtime.models import AgentIdentity
from cloud.app.agents.base_agent import AgentContext, AgentResponse, BaseAgent

logger = logging.getLogger(__name__)

__all__ = ["SuggestionResult", "SuggestionAgent"]


@dataclass
class SuggestionResult:
    """销售策略建议结果，包含策略类型、关键发现与建议行动。"""

    strategy_type: str = ""
    key_findings: list[str] = field(default_factory=list)
    suggested_actions: list[str] = field(default_factory=list)


class SuggestionAgent(BaseAgent):
    """销售策略建议 Agent，集成 HCP 画像、拜访历史与竞品情报生成策略建议。"""

    def __init__(
        self,
        identity: AgentIdentity,
        hcp_service: Any = None,
        visit_service: Any = None,
        competitor_tools: Any = None,
        llm_service: Any = None,
    ) -> None:
        self._identity = identity
        self._hcp_service = hcp_service
        self._visit_service = visit_service
        self._competitor_tools = competitor_tools
        self._llm = llm_service

    async def execute(self, context: AgentContext) -> AgentResponse:
        """执行销售策略建议生成，返回结构化 SuggestionResult 嵌入 AgentResponse。

        流程：解析 HCP ID → 收集 HCP 画像/拜访历史/竞品情报 → 调用 LLM 生成建议。
        """
        agent_id = self._identity.key
        agent_name = self._identity.name
        logger.info("SuggestionAgent(%s) execute: %s", agent_id, context.message[:64])

        hcp_id = self._extract_hcp_id(context)
        if not hcp_id:
            return AgentResponse(
                reply=json.dumps(
                    {
                        "strategy_type": "error",
                        "key_findings": ["无法从消息中解析 HCP ID"],
                        "suggested_actions": ["请提供有效的 HCP ID"],
                    },
                    ensure_ascii=False,
                ),
            )

        hcp_profile = await self._fetch_hcp_profile(hcp_id)
        visit_history = await self._fetch_visit_history(hcp_id)
        competitor_intel = await self._fetch_competitor_intel(hcp_id)

        prompt = self._build_prompt(hcp_id, hcp_profile, visit_history, competitor_intel)
        llm_reply = await self._call_llm(prompt)

        result = self._parse_result(llm_reply)
        return AgentResponse(
            reply=json.dumps(
                {
                    "strategy_type": result.strategy_type,
                    "key_findings": result.key_findings,
                    "suggested_actions": result.suggested_actions,
                },
                ensure_ascii=False,
            ),
            actions=[
                {
                    "agent": agent_name,
                    "hcp_id": hcp_id,
                    "strategy_type": result.strategy_type,
                },
            ],
            memory_updates=[],
        )

    def capabilities(self) -> list[str]:
        """返回 identity 允许的工具列表。"""
        return list(self._identity.allowed_tools)

    def _extract_hcp_id(self, context: AgentContext) -> str | None:
        """从 context 中解析 HCP ID。"""
        import re

        message = context.message
        match = re.search(r'hcp_id[=:]\s*["\']?(\w[\w-]*\w)["\']?', message)
        if match:
            return match.group(1)
        try:
            data = json.loads(message)
            return data.get("hcp_id")
        except (json.JSONDecodeError, TypeError):
            return None

    async def _fetch_hcp_profile(self, hcp_id: str) -> dict:
        """调用 hcp_service 获取 HCP 画像（科室/处方习惯/偏好渠道）。"""
        if self._hcp_service is None:
            return {}
        try:
            profile = self._hcp_service.get_profile(hcp_id)
            if profile is None:
                profile = {}
            return profile if isinstance(profile, dict) else {}
        except Exception:
            logger.exception("Failed to fetch HCP profile for %s", hcp_id)
            return {}

    async def _fetch_visit_history(self, hcp_id: str) -> list[dict]:
        """调用 visit_service 获取最近拜访历史。"""
        if self._visit_service is None:
            return []
        try:
            visits = self._visit_service.list_visits()
            return [v for v in visits if str(v.get("hcp_id", "")) == str(hcp_id)]
        except Exception:
            logger.exception("Failed to fetch visit history for %s", hcp_id)
            return []

    async def _fetch_competitor_intel(self, hcp_id: str) -> dict:
        """调用 competitor_tools 获取竞品动态。"""
        if self._competitor_tools is None:
            return {}
        try:
            comparison = self._competitor_tools.competitive_comparison(
                ["prod-001", "prod-002", "prod-003"],
            )
            strategy = self._competitor_tools.strategy_suggestion(
                "prod-001",
                ["prod-002", "prod-003"],
            )
            return {"comparison": comparison, "strategy_suggestion": strategy}
        except Exception:
            logger.exception("Failed to fetch competitor intel for %s", hcp_id)
            return {}

    def _build_prompt(
        self,
        hcp_id: str,
        hcp_profile: dict,
        visit_history: list[dict],
        competitor_intel: dict,
    ) -> str:
        """组装 prompt，包含 HCP 画像、拜访历史与竞品情报。"""
        lines = [
            f"你是一个 {self._identity.name}，负责: {self._identity.role}：{self._identity.goal}",
            "",
            "=== HCP 画像 ===",
            json.dumps(hcp_profile, ensure_ascii=False, default=str),
            "",
            "=== 最近拜访历史 ===",
            json.dumps(visit_history, ensure_ascii=False, default=str),
            "",
            "=== 竞品动态 ===",
            json.dumps(competitor_intel, ensure_ascii=False, default=str),
            "",
            "请基于以上信息生成销售策略建议，返回 JSON 格式：",
            '{ "strategy_type": "策略类型", "key_findings": ["关键发现1", "关键发现2"], "suggested_actions": ["建议行动1", "建议行动2"] }',
        ]
        return "\n".join(lines)

    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM 生成建议。"""
        if self._llm is None:
            return json.dumps(
                {
                    "strategy_type": "standard",
                    "key_findings": ["无 LLM 服务可用，使用默认策略"],
                    "suggested_actions": ["请配置 LLM 服务后重试"],
                },
                ensure_ascii=False,
            )
        try:
            return await self._llm.generate(prompt)
        except Exception:
            logger.exception("LLM call failed")
            return json.dumps(
                {
                    "strategy_type": "fallback",
                    "key_findings": ["LLM 调用失败，使用兜底策略"],
                    "suggested_actions": ["请稍后重试"],
                },
                ensure_ascii=False,
            )

    def _parse_result(self, llm_reply: str) -> SuggestionResult:
        """解析 LLM 返回结果为 SuggestionResult。"""
        try:
            data = json.loads(llm_reply)
            if isinstance(data, dict):
                return SuggestionResult(
                    strategy_type=data.get("strategy_type", "standard"),
                    key_findings=data.get("key_findings", []),
                    suggested_actions=data.get("suggested_actions", []),
                )
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
        return SuggestionResult(
            strategy_type="standard",
            key_findings=["未能解析 LLM 返回结果"],
            suggested_actions=["请重试"],
        )
