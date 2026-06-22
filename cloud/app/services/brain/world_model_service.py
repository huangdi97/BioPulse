"""世界模型 — 后台认知循环，读namespace找跨域模式关联。"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CognitionEntry:
    """认知声明——世界模型发现的跨域模式关联。"""

    cognition_id: str
    pattern: str
    description: str
    confidence: float  # 0-1
    evidence: list[str]  # 来源namespace路径
    agent_keys: list[str]  # 涉及Agent
    detected_at: str
    expires_at: str

    def to_dict(self) -> dict:
        return {
            "cognition_id": self.cognition_id,
            "pattern": self.pattern,
            "description": self.description,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "agent_keys": self.agent_keys,
            "detected_at": self.detected_at,
            "expires_at": self.expires_at,
        }


class WorldModelService:
    """世界模型——跨域模式发现引擎。

    定时读取各Agent namespace的输出，寻找跨域模式关联。
    当前实现为基于规则的关联发现，远期演进为共享表征的领域模型。
    """

    def __init__(self):
        self._cognitions: dict[str, CognitionEntry] = {}
        self._last_full_scan: Optional[str] = None

    def full_scan(self) -> list[CognitionEntry]:
        """全量扫描——触发世界模型后台循环全量扫描。"""
        from cloud.app.agent_runtime.memory.world_model import get_world_model

        get_world_model()._full_scan()
        now = datetime.now(timezone.utc).isoformat()
        self._last_full_scan = now
        cognitions = self.get_cognitions(min_confidence=0.0)
        logger.info("世界模型全量扫描完成: %d 条认知发现", len(cognitions))
        return cognitions

    def incremental_scan(self, changed_namespaces: list[str]) -> list[CognitionEntry]:
        """增量扫描——namespace变更后触发。"""
        if not changed_namespaces:
            return []
        from cloud.app.agent_runtime.memory.world_model import get_world_model

        get_world_model()._incremental_scan(changed_namespaces)
        return self.get_cognitions(min_confidence=0.0)

    def get_cognitions(
        self,
        min_confidence: float = 0.0,
        agent_key: Optional[str] = None,
        limit: int = 20,
    ) -> list[CognitionEntry]:
        """获取认知列表，支持过滤。从 SharedState 的 shared.cognition namespace 读取。"""
        from cloud.app.agent_runtime.core.shared_state import get_shared_state

        ss = get_shared_state()
        entries = ss.read("shared.cognition", min_confidence=min_confidence)
        results = []
        for e in entries:
            val = e.value if isinstance(e.value, dict) else {}
            agent_keys = val.get("agent_keys", [])
            if agent_key and agent_key not in agent_keys:
                continue
            results.append(
                CognitionEntry(
                    cognition_id=e.key,
                    pattern=val.get("pattern", ""),
                    description=val.get("description", ""),
                    confidence=e.confidence,
                    evidence=e.evidence,
                    agent_keys=agent_keys,
                    detected_at=e.timestamp or "",
                    expires_at="",
                )
            )
        results.sort(key=lambda x: (x.confidence, x.detected_at), reverse=True)
        return results[:limit]
