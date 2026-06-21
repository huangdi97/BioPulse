"""世界模型 — 后台认知循环，读namespace找跨域模式关联。"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

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
        """全量扫描——读所有可用数据，找模式关联。

        当前实现基于占位数据，对接实际namespace后替换。
        """
        now = datetime.now(timezone.utc).isoformat()
        findings: list[CognitionEntry] = []

        # 模拟扫描：从各领域数据发现关联模式
        # 实际实现中会读取 compliance.* / intelligence.* / strategy.* / bidding.* 等namespace
        mock_patterns = self._generate_mock_patterns()
        for p in mock_patterns:
            entry = CognitionEntry(
                cognition_id=uuid4().hex[:12],
                pattern=p["pattern"],
                description=p["description"],
                confidence=p["confidence"],
                evidence=p["evidence"],
                agent_keys=p["agent_keys"],
                detected_at=now,
                expires_at=datetime.now(timezone.utc).isoformat(),
            )
            self._cognitions[entry.cognition_id] = entry
            findings.append(entry)

        self._last_full_scan = now
        logger.info("世界模型全量扫描完成: %d 条认知发现", len(findings))
        return findings

    def incremental_scan(self, changed_namespaces: list[str]) -> list[CognitionEntry]:
        """增量扫描——namespace变更后触发。"""
        if not changed_namespaces:
            return []
        return self.full_scan()

    def get_cognitions(
        self,
        min_confidence: float = 0.0,
        agent_key: Optional[str] = None,
        limit: int = 20,
    ) -> list[CognitionEntry]:
        """获取认知列表，支持过滤。"""
        results = [c for c in self._cognitions.values() if c.confidence >= min_confidence and (agent_key is None or agent_key in c.agent_keys)]
        results.sort(key=lambda x: (x.confidence, x.detected_at), reverse=True)
        return results[:limit]

    def _generate_mock_patterns(self) -> list[dict]:
        """生成模拟模式（用于演示，实际namespace对接后替换）。"""
        return [
            {
                "pattern": "华北区合规评分下降 + 竞品C获批 + 拜访频率增加",
                "description": "华北区正在经历竞品冲击，合规压力增大。建议关注竞品C的区域推广策略。",
                "confidence": 0.78,
                "evidence": ["compliance.华北区.评分趋势", "intelligence.竞品C.获批", "strategy.拜访.频率分布"],
                "agent_keys": ["compliance_monitor", "competitor_crawler", "sales_suggestion"],
            },
            {
                "pattern": "张代表费用上升 + 拜访量持平 + 流向下降",
                "description": "张代表投入产出比持续下降，费用效率需重点关注。",
                "confidence": 0.65,
                "evidence": ["compliance.张代表.费用趋势", "compliance.张代表.拜访趋势", "compliance.张代表.流向趋势"],
                "agent_keys": ["compliance_monitor", "anomaly_analysis"],
            },
            {
                "pattern": "集采政策更新 + 多区域暂停招标 + 合规规则修改",
                "description": "全国多地受集采政策影响，合规规则需同步调整排除闸配置。",
                "confidence": 0.55,
                "evidence": ["intelligence.集采.政策更新", "bidding.多区域.暂停", "compliance.规则.修改日志"],
                "agent_keys": ["competitor_crawler", "opportunity_scanner", "compliance_monitor"],
            },
        ]
