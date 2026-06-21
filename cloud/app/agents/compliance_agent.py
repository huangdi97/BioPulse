"""ComplianceAgent — 规则引擎驱动的合规审核 Agent，不调用 LLM。"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

from cloud.app.agent_runtime.models import AgentIdentity
from cloud.app.agents.base_agent import AgentContext, AgentResponse, BaseAgent
from cloud.app.compliance.red_light import RedLightManager
from cloud.app.compliance.triangulation import TriangulationEngine

logger = logging.getLogger(__name__)

__all__ = ["ComplianceAgent"]


class ComplianceAgent(BaseAgent):
    """规则引擎驱动的合规审核 Agent。

    解析 context.message 提取 visit_id / expense_id，调用三角验证引擎
    进行数据交叉核验，触发红/绿灯决策并记录审计日志。
    """

    def __init__(
        self,
        identity: AgentIdentity,
        compliance_service: Any,
        triangulation_engine: TriangulationEngine,
        red_light: Optional[RedLightManager] = None,
    ) -> None:
        self._identity = identity
        self._compliance_service = compliance_service
        self._triangulation_engine = triangulation_engine
        self._red_light = red_light or RedLightManager()

    async def execute(self, context: AgentContext) -> AgentResponse:
        """执行合规审核，纯规则引擎路径，不调用 LLM。"""
        agent_id = self._identity.key
        agent_name = self._identity.name
        message = context.message

        logger.info("ComplianceAgent(%s) execute: %s", agent_id, message[:64])

        visit_id = self._extract_id(message, r"visit_id[=:]?\s*(\d+)")
        expense_id = self._extract_id(message, r"expense_id[=:]?\s*(\d+)")
        entity_id = visit_id or expense_id
        entity_type = "visit" if visit_id else ("expense" if expense_id else "unknown")

        if entity_id is None:
            return AgentResponse(
                reply=f"[{agent_name}] 无法从消息中解析 visit_id 或 expense_id，请提供有效 ID。",
            )

        expense_data = {"visit_id": visit_id} if visit_id else None
        visit_data = {"visit_id": visit_id, "expense_id": expense_id} if (visit_id or expense_id) else None
        distribution_data = None

        try:
            result = self._triangulation_engine.check(
                expense_data=expense_data,
                visit_data=visit_data,
                distribution_data=distribution_data,
            )
        except Exception:
            logger.exception("TriangulationEngine.check 失败，entity_id=%s", entity_id)
            return AgentResponse(
                reply=f"[{agent_name}] 三角验证引擎异常，请稍后重试。",
            )

        decisions = []
        if not result.passed:
            decisions.append(
                {
                    "finding": [f.to_dict() if hasattr(f, "to_dict") else str(f) for f in result.findings],
                    "confidence": result.confidence_score,
                    "level": result.suspicion_level,
                    "decision": result.decision,
                }
            )
            try:
                event = self._red_light.trigger(
                    agent_key=agent_id,
                    finding_key=f"{entity_type}:{entity_id}",
                    score=result.confidence_score,
                    detail=result.recommended_action or "triangulation_failure",
                )
                logger.info("RedLight triggered: %s", event)
            except Exception:
                logger.exception("RedLightManager.trigger 失败")

        self._write_audit_log(
            entity_type=entity_type,
            entity_id=entity_id,
            action="compliance_check",
            detail=f"三角验证 {'通过' if result.passed else '异常'}，决策={result.decision}",
        )

        reply_parts = [
            f"[{agent_name}] 合规审核完成。",
            f"状态: {'通过' if result.passed else '异常'}",
            f"置信度: {result.confidence_score}",
            f"决策: {result.decision}",
        ]
        if result.findings:
            reply_parts.append(f"发现异常项数: {len(result.findings)}")
        if result.suspicion_level:
            reply_parts.append(f"疑似等级: {result.suspicion_level}")

        return AgentResponse(
            reply="\n".join(reply_parts),
            actions=decisions,
            memory_updates=[],
        )

    def capabilities(self) -> list[str]:
        return list(self._identity.allowed_tools)

    def _extract_id(self, message: str, pattern: str) -> Optional[int]:
        match = re.search(pattern, message)
        if match:
            return int(match.group(1))
        return None

    def _write_audit_log(
        self,
        entity_type: str,
        entity_id: int,
        action: str,
        detail: str,
    ) -> None:
        try:
            svc = self._compliance_service._audit_log
            db = getattr(svc, "_connection", lambda: None)()
            if db:
                from cloud.app.repositories.compliance_repository import (
                    ComplianceAuditRecordsRepository,
                )

                repo = ComplianceAuditRecordsRepository(db)
                repo.create(
                    {
                        "entity_type": entity_type,
                        "entity_id": entity_id,
                        "action": action,
                        "detail": detail,
                    }
                )
        except Exception:
            logger.exception("写入合规审计日志失败")
