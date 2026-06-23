"""Agent 实体 — 从 identity.yaml 加载并持有运行时组件引用。"""

import logging
import os
from pathlib import Path

import yaml

from cloud.app.agent_runtime.core.model_router import ModelRouter
from cloud.app.agent_runtime.core.models import AgentIdentity, Insight
from cloud.app.agent_runtime.memory.memory import Memory
from cloud.app.agent_runtime.safety.cost_governor import CostGovernor
from cloud.app.agent_runtime.safety.safety_guard import SafetyGuard
from cloud.app.agent_runtime.tools.tool_bridge import ToolBridge

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
        """Generate contextual insights based on agent type and page."""
        key = self.identity.key

        if key == "compliance_monitor":
            return await self._compliance_insights(page_id, user_id)
        elif key == "sales_suggestion":
            return await self._suggestion_insights(page_id, user_id)
        elif key == "anomaly_analysis":
            return await self._anomaly_insights(page_id, user_id)
        elif key == "knowledge_worker":
            return await self._knowledge_insights(page_id, user_id)
        elif key == "opportunity_scanner":
            return await self._opportunity_insights(page_id, user_id)
        else:
            return []

    async def _compliance_insights(self, page_id: str, user_id: str) -> list[Insight]:
        """Query compliance data for real insights."""
        try:
            from cloud.app.services.compliance_svc.decision_intel_service import DecisionIntelService

            svc = DecisionIntelService()
            dashboard = svc.dashboard()
            total = dashboard.get("total_cases", 0)
            red_flags = dashboard.get("red_flag_count", 0) if isinstance(dashboard, dict) else 0
            insights = []
            if total > 0:
                insights.append(
                    Insight(
                        agent_key=self.identity.key,
                        page_id=page_id,
                        summary=f"合规监控中：{total} 个案件，{red_flags} 个红灯",
                        details={"total_cases": total, "red_flags": red_flags},
                        confidence=0.9,
                    )
                )
            return insights
        except Exception:
            return []

    async def _suggestion_insights(self, page_id: str, user_id: str) -> list[Insight]:
        """Query visit/HCP data for suggestion insights."""
        try:
            from cloud.app.services.rep_workbench.visit_service import VisitService

            svc = VisitService()
            visits = svc.list_visits()
            count = len(visits) if isinstance(visits, list) else 0
            if count > 0:
                return [
                    Insight(
                        agent_key=self.identity.key,
                        page_id=page_id,
                        summary=f"近期 {count} 条拜访记录，可基于拜访历史生成策略建议",
                        details={"visit_count": count},
                        confidence=0.85,
                    )
                ]
            return []
        except Exception:
            return []

    async def _anomaly_insights(self, page_id: str, user_id: str) -> list[Insight]:
        """Query anomaly/context data."""
        try:
            from cloud.app.services.platform_svc.anomaly_context_service import AnomalyContextService

            svc = AnomalyContextService()
            if hasattr(svc, "list_anomalies"):
                anomalies = svc.list_anomalies()
                count = len(anomalies) if isinstance(anomalies, list) else 0
                if count > 0:
                    return [
                        Insight(
                            agent_key=self.identity.key,
                            page_id=page_id,
                            summary=f"检测到 {count} 条异常模式，可展开根因分析",
                            details={"anomaly_count": count},
                            confidence=0.8,
                        )
                    ]
            return []
        except Exception:
            return []

    async def _knowledge_insights(self, page_id: str, user_id: str) -> list[Insight]:
        """Query knowledge graph for entity insights."""
        try:
            from cloud.app.services.brain.kg_service import KGService

            svc = KGService()
            dashboard = svc.dashboard()
            entity_count = dashboard.get("entity_count", 0) if isinstance(dashboard, dict) else 0
            rel_count = dashboard.get("relation_count", 0) if isinstance(dashboard, dict) else 0
            if entity_count > 0:
                return [
                    Insight(
                        agent_key=self.identity.key,
                        page_id=page_id,
                        summary=f"知识图谱：{entity_count} 实体，{rel_count} 关系，可探索关联",
                        details={"entities": entity_count, "relations": rel_count},
                        confidence=0.85,
                    )
                ]
            return []
        except Exception:
            return []

    async def _opportunity_insights(self, page_id: str, user_id: str) -> list[Insight]:
        """Query pipeline/opportunity data."""
        try:
            from cloud.app.services.rep_workbench.opportunity_service import OpportunityService

            svc = OpportunityService()
            pipeline = svc.get_pipeline()
            total_value = pipeline.get("total_value", 0) if isinstance(pipeline, dict) else 0
            stage_count = pipeline.get("stage_count", 0) if isinstance(pipeline, dict) else 0
            if stage_count and stage_count > 0:
                return [
                    Insight(
                        agent_key=self.identity.key,
                        page_id=page_id,
                        summary=f"管线总额 ¥{total_value:,.0f}，{stage_count} 个商机待推进",
                        details={"total_value": total_value, "stage_count": stage_count},
                        confidence=0.9,
                    )
                ]
            return []
        except Exception:
            return []
