"""Structured Handoff — Agent 间通过结构化文档（PRD/设计/报告）传递信息，取代自由聊天。"""

import logging
from typing import Any

from cloud.app.agent_runtime.core.shared_state import SharedStateEntry, get_shared_state

logger = logging.getLogger(__name__)

ARTIFACT_TYPES = {
    "compliance_report": {"required": ["hcp", "score", "issues", "recommendation"]},
    "visit_plan": {"required": ["hcp", "objectives", "priority", "scheduled_date"]},
    "competitor_brief": {"required": ["competitor", "drug", "activity", "impact"]},
    "expense_audit": {"required": ["report_id", "total", "flags", "verdict"]},
    "insight_card": {"required": ["title", "summary", "confidence", "source"]},
}


class StructuredHandoffError(Exception):
    """structured handoff error."""


class StructuredHandoff:
    """Agent 产出结构化文档 → 下一个 Agent 按类型消费。每个 artifact 有固定 schema。"""

    HANDSHAKE_NAMESPACE = "handoff"

    def produce(self, agent_key: str, artifact_type: str, content: dict[str, Any]) -> str:
        """产出结构化文档，写入 SharedState handoff namespace。"""
        schema = ARTIFACT_TYPES.get(artifact_type)
        if schema is None:
            raise StructuredHandoffError(f"Unknown artifact type: {artifact_type}")

        missing = [f for f in schema["required"] if f not in content]
        if missing:
            raise StructuredHandoffError(f"Missing required fields {missing} for {artifact_type}")

        artifact_id = f"{artifact_type}/{agent_key}"
        entry = SharedStateEntry(
            namespace=self.HANDSHAKE_NAMESPACE,
            key=f"artifact.{artifact_id}",
            value={
                "artifact_type": artifact_type,
                "producer": agent_key,
                "content": content,
                "status": "ready",
            },
            agent_key=agent_key,
        )
        get_shared_state().write(entry, caller_agent_key=agent_key)
        logger.info("Artifact produced: %s by %s", artifact_id, agent_key)
        return artifact_id

    def consume(self, target_agent_key: str, artifact_type: str) -> dict[str, Any] | None:
        """读取指定类型的上游结构化文档。"""
        ss = get_shared_state()
        entries = ss.read(namespace=self.HANDSHAKE_NAMESPACE)
        for e in entries:
            if not e.key.startswith(f"artifact.{artifact_type}"):
                continue
            val = e.value
            if isinstance(val, dict) and val.get("status") == "ready":
                return val.get("content", {})
        return None

    def list_available(self) -> list[dict[str, Any]]:
        """列出所有可消费的结构化文档。"""
        ss = get_shared_state()
        entries = ss.read(namespace=self.HANDSHAKE_NAMESPACE)
        result: list[dict[str, Any]] = []
        for e in entries:
            val = e.value
            if isinstance(val, dict) and val.get("status") == "ready":
                result.append(
                    {
                        "artifact_id": e.key.removeprefix("artifact."),
                        "artifact_type": val.get("artifact_type"),
                        "producer": val.get("producer"),
                    }
                )
        return result

    def mark_consumed(self, artifact_id: str, consumer: str) -> None:
        """标记文档已被消费。"""
        entry = SharedStateEntry(
            namespace=self.HANDSHAKE_NAMESPACE,
            key=f"artifact.{artifact_id}",
            value={"status": "consumed", "consumer": consumer},
            agent_key=consumer,
        )
        get_shared_state().write(entry, caller_agent_key=consumer)
