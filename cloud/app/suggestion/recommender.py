"""策略推荐与多方案生成模块。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .collector import CollectionResult


@dataclass(slots=True)
class Strategy:
    """单个销售策略方案。

    Attributes:
        strategy_id: 策略唯一标识。
        name: 策略名称。
        objective: 策略目标。
        actions: 推荐行动列表。
        confidence: 置信度评分。
        reasoning_chain: 推理链。
        risk_notes: 风险提示。
    """

    strategy_id: str
    name: str
    objective: str
    actions: list[str]
    confidence: float
    reasoning_chain: list[str]
    risk_notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class StrategySet:
    """策略集合。

    Attributes:
        context: 原始触发上下文。
        strategies: 可选策略列表。
        recommended_strategy_id: 推荐优先采用的策略 ID。
        evidence_summary: 证据摘要。
    """

    context: dict[str, Any]
    strategies: list[Strategy]
    recommended_strategy_id: str
    evidence_summary: dict[str, Any]


class StrategyRecommender:
    """根据收集结果生成多策略建议。"""

    def recommend(self, context: dict[str, Any], collection_result: CollectionResult) -> StrategySet:
        """生成不少于三个可选策略。

        Args:
            context: 触发上下文。
            collection_result: 信息收集结果。

        Returns:
            包含候选策略、评分和推理链的 StrategySet。
        """
        evidence = self._build_evidence(collection_result)
        strategies = [
            self._new_product_strategy(evidence),
            self._portfolio_defense_strategy(evidence),
            self._academic_support_strategy(evidence),
        ]
        strategies.sort(key=lambda item: item.confidence, reverse=True)
        return StrategySet(
            context=dict(context),
            strategies=strategies,
            recommended_strategy_id=strategies[0].strategy_id,
            evidence_summary=evidence,
        )

    def _build_evidence(self, collection_result: CollectionResult) -> dict[str, Any]:
        """提取策略推荐所需证据摘要。

        Args:
            collection_result: 信息收集结果。

        Returns:
            归一化证据摘要。
        """
        profile = collection_result.data.get("hcp_profile", {})
        visits = collection_result.data.get("visit_history", {})
        competitor = collection_result.data.get("competitor_intel", {})
        market = collection_result.data.get("market_intel", {})
        causal = collection_result.causal_result or {}
        return {
            "hcp_score": float(profile.get("unified_score", 70) or 70),
            "specialty": profile.get("specialty", ""),
            "visit_count": int(visits.get("visit_count", 0) or 0),
            "competitor_events": self._competitor_event_count(competitor),
            "high_impact_market": int(market.get("high_impact_count", 0) or 0),
            "causal_confidence": self._avg_causal_confidence(causal),
            "completed_sources": list(collection_result.completed_steps),
            "failed_sources": dict(collection_result.failed_steps),
        }

    def _new_product_strategy(self, evidence: dict[str, Any]) -> Strategy:
        """生成推新品策略。

        Args:
            evidence: 证据摘要。

        Returns:
            推新品策略。
        """
        confidence = self._score(0.52, evidence["hcp_score"] / 200, evidence["high_impact_market"] * 0.04)
        return Strategy(
            strategy_id="new_product_push",
            name="推新品",
            objective="基于 HCP 专长和市场热点引入新品/新适应症价值信息。",
            actions=[
                "围绕科室关注疾病场景准备新品差异化价值点。",
                "使用近期市场情报中的高影响信号作为开场依据。",
                "将下一步安排为小范围病例讨论或资料递送。",
            ],
            confidence=confidence,
            reasoning_chain=[
                f"HCP统一评分为 {evidence['hcp_score']:.1f}，具备新品教育优先级。",
                f"市场高影响情报 {evidence['high_impact_market']} 条，可支撑新品切入。",
                f"因果推断平均置信度 {evidence['causal_confidence']:.2f}。",
            ],
            risk_notes=["避免夸大适应症或疗效边界，所有材料需使用已审批版本。"],
        )

    def _portfolio_defense_strategy(self, evidence: dict[str, Any]) -> Strategy:
        """生成巩固存量策略。

        Args:
            evidence: 证据摘要。

        Returns:
            巩固存量策略。
        """
        confidence = self._score(0.5, min(evidence["visit_count"], 5) * 0.05, evidence["competitor_events"] * 0.03)
        return Strategy(
            strategy_id="portfolio_defense",
            name="巩固存量",
            objective="稳定既有产品认知和处方习惯，降低竞品扰动。",
            actions=[
                "复盘上次拜访共识，确认当前产品使用阻碍。",
                "针对竞品动作准备差异化、合规的对照话术。",
                "约定后续跟进节点，保持关系连续性。",
            ],
            confidence=confidence,
            reasoning_chain=[
                f"历史拜访 {evidence['visit_count']} 次，适合延续既有沟通链路。",
                f"竞品动态 {evidence['competitor_events']} 个，需要防御性信息更新。",
                "关系连续性是存量巩固的关键正向因子。",
            ],
            risk_notes=["竞品比较应限定在公开、可验证和合规批准的信息范围内。"],
        )

    def _academic_support_strategy(self, evidence: dict[str, Any]) -> Strategy:
        """生成学术支持策略。

        Args:
            evidence: 证据摘要。

        Returns:
            学术支持策略。
        """
        specialty_bonus = 0.08 if evidence.get("specialty") else 0.0
        confidence = self._score(0.48, evidence["causal_confidence"] * 0.2, specialty_bonus)
        return Strategy(
            strategy_id="academic_support",
            name="学术支持",
            objective="通过指南、病例和会议资源提升 HCP 对治疗路径的认可。",
            actions=[
                "匹配 HCP 专长准备指南更新或病例资料。",
                "邀请参加线上/线下学术活动，记录兴趣点。",
                "将异议转化为下一次学术材料跟进任务。",
            ],
            confidence=confidence,
            reasoning_chain=[
                f"HCP专长为 {evidence.get('specialty') or '未明确'}，可进行内容匹配。",
                f"因果推断置信度 {evidence['causal_confidence']:.2f} 支持学术干预评估。",
                "学术支持适合在新品与存量策略之外补足长期信任。",
            ],
            risk_notes=["学术活动邀约必须符合合规边界，避免与处方承诺绑定。"],
        )

    def _competitor_event_count(self, competitor: dict[str, Any]) -> int:
        """统计竞品事件数量。

        Args:
            competitor: 竞品情报摘要。

        Returns:
            事件数量。
        """
        summary = competitor.get("summary", {})
        return int(summary.get("new_product_launches", 0) or 0) + int(summary.get("marketing_activities", 0) or 0)

    def _avg_causal_confidence(self, causal: dict[str, Any]) -> float:
        """计算因果推断平均置信度。

        Args:
            causal: 因果推断输出。

        Returns:
            平均置信度。
        """
        simulations = causal.get("simulations", [])
        if not simulations:
            return 0.5
        return round(sum(float(item.get("confidence", 0.5)) for item in simulations) / len(simulations), 4)

    def _score(self, base: float, *signals: float) -> float:
        """生成 0 到 0.95 区间内的置信度评分。

        Args:
            base: 基础分。
            signals: 增量信号。

        Returns:
            归一化置信度。
        """
        return round(min(0.95, max(0.1, base + sum(signals))), 4)
