"""Agent 实体 — 从 identity.yaml 加载并持有运行时组件引用。"""

import logging
import os
from pathlib import Path

import yaml

from cloud.app.agent_runtime.core.model_router import ModelRouter
from cloud.app.agent_runtime.core.models import AgentIdentity, Insight
from cloud.app.agent_runtime.core.shared_state import SharedStateEntry, get_shared_state
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
            return await self._compliance_autonomous_cycle(page_id, user_id)
        elif key == "sales_suggestion":
            return await self._suggestion_insights(page_id, user_id)
        elif key == "anomaly_analysis":
            return await self._anomaly_autonomous_cycle(page_id, user_id)
        elif key == "knowledge_worker":
            return await self._knowledge_insights(page_id, user_id)
        elif key == "opportunity_scanner":
            return await self._opportunity_autonomous_cycle(page_id, user_id)
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
                ss = get_shared_state()
                evidence = [
                    "来源: DecisionIntelService.dashboard",
                    f"数据: total_cases={total}, red_flags={red_flags}",
                    f"计算: red_flag_rate={red_flags / max(total, 1):.1%}",
                ]
                ss.write(
                    SharedStateEntry(
                        namespace="compliance.result",
                        key=f"insights_{page_id}_{user_id}",
                        value={"summary": f"合规监控中：{total} 个案件，{red_flags} 个红灯", "total_cases": total, "red_flags": red_flags},
                        confidence=0.9,
                        agent_key=self.identity.key,
                        evidence=evidence,
                    ),
                    caller_agent_key=self.identity.key,
                )
            return insights
        except Exception:
            return []

    async def _compliance_autonomous_cycle(self, page_id: str, user_id: str) -> list[Insight]:
        """L4 自主行动循环: discover → collect_evidence → classify → notify.

        保持旧接口 _compliance_insights 供向后兼容。
        """
        try:
            from cloud.app.agent_runtime.comm.notifier import Notifier
            from cloud.app.services.compliance_svc.decision_intel_service import DecisionIntelService

            svc = DecisionIntelService()
            dashboard = svc.dashboard()
            total = dashboard.get("total_cases", 0)
            red_flags = dashboard.get("red_flag_count", 0) if isinstance(dashboard, dict) else 0

            # discover: 获取 red_light 案件
            red_light_cases = []
            if hasattr(svc, "list_red_light_cases"):
                red_light_cases = svc.list_red_light_cases() or []
            elif isinstance(dashboard, dict):
                red_light_cases = dashboard.get("red_light_cases", [])

            insights = []
            if total > 0:
                base_evidence = [
                    "来源: DecisionIntelService.dashboard",
                    f"数据: total_cases={total}, red_flags={red_flags}",
                    f"计算: red_flag_rate={red_flags / max(total, 1):.1%}",
                ]
                ss = get_shared_state()
                classified = {"low": [], "medium": [], "high": [], "critical": []}
                notifications = []

                for case in red_light_cases[:20]:
                    case_id = case.get("case_id", "") if isinstance(case, dict) else str(case)
                    case_desc = case.get("description", "") if isinstance(case, dict) else str(case)
                    severity_str = case.get("severity", "medium") if isinstance(case, dict) else "medium"

                    # collect_evidence: 关联查询拜访记录、费用、HCP
                    evidence_items = [f"案件: {case_id}"]
                    try:
                        from cloud.app.services.rep_workbench.visit_service import VisitService

                        vs = VisitService()
                        if hasattr(vs, "query_by_case"):
                            visit_data = vs.query_by_case(case_id)
                            evidence_items.append(f"关联拜访: {visit_data}")
                    except Exception:
                        evidence_items.append("关联拜访: 查询失败")

                    # classify: 按严重程度
                    severity = "critical" if severity_str == "critical" else severity_str
                    if severity not in classified:
                        severity = "medium"
                    classified[severity].append(case_id)

                    # collect_evidence → SharedState 写入
                    case_confidence = {"critical": 0.95, "high": 0.85, "medium": 0.7, "low": 0.5}.get(severity, 0.7)
                    ss.write(
                        SharedStateEntry(
                            namespace="compliance.result",
                            key=f"red_light_{case_id}",
                            value={"case_id": case_id, "description": case_desc, "severity": severity},
                            confidence=case_confidence,
                            agent_key=self.identity.key,
                            evidence=evidence_items,
                        ),
                        caller_agent_key=self.identity.key,
                    )

                    # notify: critical 走审批队列，其余 in-app 通知
                    notifier = Notifier()
                    if severity == "critical":
                        request_id = notifier.send_approval_request(
                            self.identity.key,
                            f"合规红灯-critial: {case_id}",
                            {"case_id": case_id, "severity": severity, "description": case_desc},
                        )
                        notifications.append(f"审批请求已发送: {request_id}")
                    else:
                        notifier.send(
                            f"[{severity.upper()}] 合规红灯: {case_id} - {case_desc[:100]}",
                            priority="high" if severity in ("high", "critical") else "normal",
                        )
                        notifications.append(f"通知已发送: {case_id}")

                summary = f"合规监控: {total} 个案件, {red_flags} 个红灯"
                if classified["critical"]:
                    summary += f", {len(classified['critical'])} 个紧急(已发起审批)"
                if classified["high"]:
                    summary += f", {len(classified['high'])} 个高危(已通知)"

                insights.append(
                    Insight(
                        agent_key=self.identity.key,
                        page_id=page_id,
                        summary=summary,
                        details={
                            "total_cases": total,
                            "red_flags": red_flags,
                            "classified": {k: len(v) for k, v in classified.items()},
                            "notifications": notifications[:5],
                        },
                        confidence=0.9,
                    )
                )
                ss.write(
                    SharedStateEntry(
                        namespace="compliance.result",
                        key=f"autonomous_cycle_{page_id}_{user_id}",
                        value={
                            "summary": summary,
                            "classified": {k: len(v) for k, v in classified.items()},
                            "notifications_sent": len(notifications),
                        },
                        confidence=0.9,
                        agent_key=self.identity.key,
                        evidence=base_evidence + [f"通知: {len(notifications)} 条已推送"],
                    ),
                    caller_agent_key=self.identity.key,
                )
            return insights
        except Exception:
            logger.exception("_compliance_autonomous_cycle failed")
            return []

    async def _suggestion_insights(self, page_id: str, user_id: str) -> list[Insight]:
        """Query visit/HCP data for suggestion insights."""
        try:
            from cloud.app.services.rep_workbench.visit_service import VisitService

            svc = VisitService()
            visits = svc.list_visits()
            count = len(visits) if isinstance(visits, list) else 0
            if count > 0:
                insights = [
                    Insight(
                        agent_key=self.identity.key,
                        page_id=page_id,
                        summary=f"近期 {count} 条拜访记录，可基于拜访历史生成策略建议",
                        details={"visit_count": count},
                        confidence=0.85,
                    )
                ]
                ss = get_shared_state()
                evidence = [
                    "来源: VisitService.list_visits",
                    f"数据: visit_count={count}",
                    "计算: 基于拜访记录完整性评估",
                ]
                ss.write(
                    SharedStateEntry(
                        namespace="suggestion.result",
                        key=f"insights_{page_id}_{user_id}",
                        value={"summary": f"近期 {count} 条拜访记录", "visit_count": count},
                        confidence=0.85,
                        agent_key=self.identity.key,
                        evidence=evidence,
                    ),
                    caller_agent_key=self.identity.key,
                )
                return insights
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
                    insights = [
                        Insight(
                            agent_key=self.identity.key,
                            page_id=page_id,
                            summary=f"检测到 {count} 条异常模式，可展开根因分析",
                            details={"anomaly_count": count},
                            confidence=0.8,
                        )
                    ]
                    ss = get_shared_state()
                    evidence = [
                        "来源: AnomalyContextService.list_anomalies",
                        f"数据: anomaly_count={count}",
                        "计算: 基于异常模式数量评估",
                    ]
                    ss.write(
                        SharedStateEntry(
                            namespace="analysis.result",
                            key=f"insights_{page_id}_{user_id}",
                            value={"summary": f"检测到 {count} 条异常模式", "anomaly_count": count},
                            confidence=0.8,
                            agent_key=self.identity.key,
                            evidence=evidence,
                        ),
                        caller_agent_key=self.identity.key,
                    )
                return insights
            return []
        except Exception:
            return []

    async def _opportunity_autonomous_cycle(self, page_id: str, user_id: str) -> list[Insight]:
        """L4 自主行动循环: detect_stalled → fetch_competitor_intel → generate_suggestion → notify.

        保持旧接口 _opportunity_insights 供向后兼容。
        """
        try:
            from datetime import datetime

            from cloud.app.agent_runtime.comm.notifier import Notifier
            from cloud.app.services.rep_workbench.opportunity_service import OpportunityService

            svc = OpportunityService()
            pipeline = svc.get_pipeline()
            total_value = pipeline.get("total_value", 0) if isinstance(pipeline, dict) else 0
            stage_count = pipeline.get("stage_count", 0) if isinstance(pipeline, dict) else 0
            opportunities = pipeline.get("opportunities", []) if isinstance(pipeline, dict) else []

            ss = get_shared_state()
            notifier = Notifier()
            insights = []
            stalled_count = 0
            suggestions = []

            for opp in opportunities[:20]:
                opp_id = opp.get("id", "") if isinstance(opp, dict) else ""
                opp_name = opp.get("name", "") if isinstance(opp, dict) else str(opp)
                stage = opp.get("stage", "") if isinstance(opp, dict) else ""
                last_activity_str = opp.get("last_activity_date", "") if isinstance(opp, dict) else ""
                owner = opp.get("owner", "") if isinstance(opp, dict) else ""
                value = opp.get("value", 0) if isinstance(opp, dict) else 0

                evidence_items = [
                    "来源: OpportunityService.get_pipeline",
                    f"商机: {opp_id} - {opp_name}",
                    f"阶段: {stage}",
                ]

                # detect_stalled: 检测超过 N 天无进展的商机
                stalled = False
                days_stalled = 0
                if last_activity_str:
                    try:
                        last_activity = datetime.fromisoformat(last_activity_str)
                        days_stalled = (datetime.now() - last_activity).days
                        if days_stalled > 30:
                            stalled = True
                            stalled_count += 1
                            evidence_items.append(f"停滞检测: {days_stalled} 天无进展")
                    except (ValueError, TypeError):
                        pass

                if not stalled:
                    continue

                # fetch_competitor_intel: 查询竞品情报
                competitor_info = "未获取"
                try:
                    from cloud.app.services.rep_workbench.visit_service import VisitService

                    vs = VisitService()
                    if hasattr(vs, "query_competitor_intel"):
                        competitor_info = vs.query_competitor_intel(opp_name) or "无竞品数据"
                        evidence_items.append(f"竞品情报: {str(competitor_info)[:100]}")
                except Exception:
                    evidence_items.append("竞品情报: 查询失败")

                # generate_suggestion: 生成推进建议
                if days_stalled > 60:
                    suggestion = "降价/转介绍：此商机已停滞超过60天，建议调整策略"
                elif days_stalled > 45:
                    suggestion = "增加拜访：此商机停滞超过45天，建议增加拜访频率"
                elif days_stalled > 30:
                    suggestion = "跟进提醒：此商机停滞超过30天，建议主动跟进"
                else:
                    suggestion = "常规跟进"

                suggestions.append(
                    {
                        "opp_id": opp_id,
                        "opp_name": opp_name,
                        "days_stalled": days_stalled,
                        "suggestion": suggestion,
                        "owner": owner,
                        "value": value,
                    }
                )
                evidence_items.append(f"建议: {suggestion}")

                # 写入 SharedState
                confidence = 0.7 if days_stalled <= 45 else (0.85 if days_stalled <= 60 else 0.95)
                ss.write(
                    SharedStateEntry(
                        namespace="opportunity.result",
                        key=f"stalled_{opp_id}",
                        value={
                            "opp_id": opp_id,
                            "opp_name": opp_name,
                            "days_stalled": days_stalled,
                            "stage": stage,
                            "owner": owner,
                            "value": value,
                            "competitor_intel": str(competitor_info)[:200],
                            "suggestion": suggestion,
                        },
                        confidence=confidence,
                        agent_key=self.identity.key,
                        evidence=evidence_items,
                    ),
                    caller_agent_key=self.identity.key,
                )

                # notify: 推送给相关销售代表
                if owner:
                    notifier.send(
                        f"[商机停滞] {opp_name} 已停滞 {days_stalled} 天 (负责人:{owner}) 建议: {suggestion}",
                        priority="high" if days_stalled > 60 else "normal",
                    )
                else:
                    notifier.send(
                        f"[商机停滞] {opp_name} 已停滞 {days_stalled} 天 建议: {suggestion}",
                        priority="high" if days_stalled > 60 else "normal",
                    )

            summary = f"管线总额 ¥{total_value:,.0f}，{stage_count} 个商机"
            if stalled_count:
                summary += f"，检测到 {stalled_count} 个停滞商机"

            if stalled_count > 0 or (stage_count and stage_count > 0):
                insights.append(
                    Insight(
                        agent_key=self.identity.key,
                        page_id=page_id,
                        summary=summary,
                        details={
                            "total_value": total_value,
                            "stage_count": stage_count,
                            "stalled_count": stalled_count,
                            "suggestions": suggestions[:5],
                        },
                        confidence=0.9,
                    )
                )
                ss.write(
                    SharedStateEntry(
                        namespace="opportunity.result",
                        key=f"autonomous_cycle_{page_id}_{user_id}",
                        value={
                            "summary": summary,
                            "stalled_count": stalled_count,
                            "suggestions_generated": len(suggestions),
                        },
                        confidence=0.9,
                        agent_key=self.identity.key,
                        evidence=["来源: OpportunityService", f"商机总数: {stage_count}", f"停滞: {stalled_count}", f"建议: {len(suggestions)} 条"],
                    ),
                    caller_agent_key=self.identity.key,
                )
            return insights
        except Exception:
            logger.exception("_opportunity_autonomous_cycle failed")
            return []

    async def _anomaly_autonomous_cycle(self, page_id: str, user_id: str) -> list[Insight]:
        """L4 自主行动循环: discover → generate_hypothesis → cross_verify → notify.

        保持旧接口 _anomaly_insights 供向后兼容。
        """
        try:
            from cloud.app.agent_runtime.analyzer.hypothesis import HypothesisEngine
            from cloud.app.agent_runtime.comm.notifier import Notifier
            from cloud.app.services.platform_svc.anomaly_context_service import AnomalyContextService

            svc = AnomalyContextService()
            if not hasattr(svc, "list_anomalies"):
                return []

            anomalies = svc.list_anomalies()
            count = len(anomalies) if isinstance(anomalies, list) else 0
            if count == 0:
                return []

            ss = get_shared_state()
            engine = HypothesisEngine()
            notifier = Notifier()
            insights = []
            hypothesis_entries = []

            for anomaly in anomalies[:10]:
                anomaly_id = anomaly.get("anomaly_id", "") if isinstance(anomaly, dict) else str(anomaly)
                anomaly_desc = anomaly.get("description", "") if isinstance(anomaly, dict) else str(anomaly)

                # discover: 获取异常模式
                anomaly_evidence = [
                    "来源: AnomalyContextService.list_anomalies",
                    f"数据: anomaly_id={anomaly_id}, description={anomaly_desc[:100]}",
                ]

                # generate_hypothesis: 调用 HypothesisEngine
                red_light_event = {"event_id": anomaly_id, "description": anomaly_desc}
                try:
                    hypothesis_result = engine.hypothesis_verification_loop(red_light_event)
                    hypotheses = hypothesis_result.get("hypotheses", [])
                    narrative = hypothesis_result.get("narrative", {})
                    hypothesis_entries.append(
                        {
                            "anomaly_id": anomaly_id,
                            "hypotheses": hypotheses,
                            "narrative": narrative.root_cause if hasattr(narrative, "root_cause") else "",
                        }
                    )
                    if hasattr(narrative, "reasoning_chain"):
                        anomaly_evidence.extend(narrative.reasoning_chain[:3])
                except Exception as e:
                    anomaly_evidence.append(f"假设生成失败: {str(e)[:100]}")

                # cross_verify: 跨 namespace 读取 compliance + visit + opportunity
                cross_evidence = []
                for ns in ["compliance.result", "visit.records", "opportunity.result"]:
                    ns_entries = ss.read(ns, min_confidence=0.3)
                    if ns_entries:
                        cross_evidence.append(f"交叉验证: {ns} 存在 {len(ns_entries)} 条相关记录")
                if cross_evidence:
                    anomaly_evidence.extend(cross_evidence[:3])

                # 计算置信度
                confidence = 0.8
                if hypothesis_entries and hypothesis_entries[-1].get("narrative"):
                    conf_val = getattr(narrative, "confidence", 0) if hasattr(narrative, "confidence") else 0
                    confidence = max(0.5, conf_val) if conf_val else 0.8
                if cross_evidence:
                    confidence = min(1.0, confidence + 0.1)

                # 写入 SharedState
                ss.write(
                    SharedStateEntry(
                        namespace="analysis.result",
                        key=f"anomaly_{anomaly_id}",
                        value={
                            "anomaly_id": anomaly_id,
                            "description": anomaly_desc,
                            "hypotheses": [h.get("description", "") for h in hypothesis_entries[-1].get("hypotheses", [])]
                            if hypothesis_entries
                            else [],
                            "root_cause": hypothesis_entries[-1].get("narrative", "") if hypothesis_entries else "",
                        },
                        confidence=confidence,
                        agent_key=self.identity.key,
                        evidence=anomaly_evidence,
                    ),
                    caller_agent_key=self.identity.key,
                )

                # 写入 hypothesis namespace
                if hypothesis_entries:
                    last_hyp = hypothesis_entries[-1]
                    for h in last_hyp.get("hypotheses", []):
                        ss.write(
                            SharedStateEntry(
                                namespace="analysis.hypothesis",
                                key=f"hyp_{h.get('id', 'unknown')}",
                                value=h,
                                confidence=h.get("confidence", 0.5),
                                agent_key=self.identity.key,
                                evidence=["来源: HypothesisEngine", f"假设: {h.get('description', '')}"],
                            ),
                            caller_agent_key=self.identity.key,
                        )

                # notify: 高置信度发现推送
                if confidence >= 0.7:
                    notifier.send(
                        f"[异常发现] {anomaly_desc[:100]} 置信度:{confidence:.0%}",
                        priority="high" if confidence >= 0.85 else "normal",
                    )

            summary = f"异常分析: {count} 个异常模式"
            if hypothesis_entries:
                confirmed = sum(1 for h in hypothesis_entries if h.get("narrative"))
                summary += f", {confirmed} 个已生成根因假设"

            insights.append(
                Insight(
                    agent_key=self.identity.key,
                    page_id=page_id,
                    summary=summary,
                    details={
                        "anomaly_count": count,
                        "hypothesis_count": len(hypothesis_entries),
                        "entries": hypothesis_entries[:5],
                    },
                    confidence=0.8,
                )
            )

            ss.write(
                SharedStateEntry(
                    namespace="analysis.result",
                    key=f"autonomous_cycle_{page_id}_{user_id}",
                    value={
                        "summary": summary,
                        "anomaly_count": count,
                        "hypothesis_count": len(hypothesis_entries),
                    },
                    confidence=0.8,
                    agent_key=self.identity.key,
                    evidence=["来源: AnomalyContextService + HypothesisEngine", f"异常数: {count}", f"假设数: {len(hypothesis_entries)}"],
                ),
                caller_agent_key=self.identity.key,
            )
            return insights
        except Exception:
            logger.exception("_anomaly_autonomous_cycle failed")
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
                insights = [
                    Insight(
                        agent_key=self.identity.key,
                        page_id=page_id,
                        summary=f"管线总额 ¥{total_value:,.0f}，{stage_count} 个商机待推进",
                        details={"total_value": total_value, "stage_count": stage_count},
                        confidence=0.9,
                    )
                ]
                ss = get_shared_state()
                evidence = [
                    "来源: OpportunityService.get_pipeline",
                    f"数据: total_value={total_value}, stage_count={stage_count}",
                    "计算: 基于管线数据完整度评估",
                ]
                ss.write(
                    SharedStateEntry(
                        namespace="opportunity.result",
                        key=f"insights_{page_id}_{user_id}",
                        value={
                            "summary": f"管线总额 ¥{total_value:,.0f}，{stage_count} 个商机",
                            "total_value": total_value,
                            "stage_count": stage_count,
                        },
                        confidence=0.9,
                        agent_key=self.identity.key,
                        evidence=evidence,
                    ),
                    caller_agent_key=self.identity.key,
                )
                return insights
            return []
        except Exception:
            return []
