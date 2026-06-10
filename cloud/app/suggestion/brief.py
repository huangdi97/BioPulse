"""Pre-call Brief 生成模块，输出结构化 JSON 与自然语言文本。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .recommender import Strategy, StrategySet


@dataclass(slots=True)
class Brief:
    """Pre-call Brief 输出。

    Attributes:
        json_payload: 结构化 JSON 负载。
        text: 自然语言简报文本。
    """

    json_payload: dict[str, Any]
    text: str


class BriefGenerator:
    """根据策略集合生成拜访前简报。"""

    def generate(self, strategy_set: StrategySet) -> Brief:
        """生成完整 Pre-call Brief。

        Args:
            strategy_set: 策略推荐集合。

        Returns:
            包含结构化 JSON 与自然语言文本的 Brief。
        """
        primary = self._primary_strategy(strategy_set)
        payload = {
            "pre_call_brief": self._pre_call_brief(strategy_set, primary),
            "competitor_talk_track": self._competitor_talk_track(primary),
            "objection_handling": self._objection_handling(primary),
            "follow_up_strategy": self._follow_up_strategy(primary),
            "strategy_options": [asdict(strategy) for strategy in strategy_set.strategies],
        }
        return Brief(json_payload=payload, text=self._render_text(payload))

    def _primary_strategy(self, strategy_set: StrategySet) -> Strategy:
        """获取推荐优先策略。

        Args:
            strategy_set: 策略推荐集合。

        Returns:
            首选策略。
        """
        for strategy in strategy_set.strategies:
            if strategy.strategy_id == strategy_set.recommended_strategy_id:
                return strategy
        return strategy_set.strategies[0]

    def _pre_call_brief(self, strategy_set: StrategySet, primary: Strategy) -> dict[str, Any]:
        """构建 Pre-call Brief 主体。

        Args:
            strategy_set: 策略推荐集合。
            primary: 首选策略。

        Returns:
            Brief 主体字典。
        """
        context = strategy_set.context
        evidence = strategy_set.evidence_summary
        return {
            "rep_id": context.get("rep_id"),
            "hcp_id": context.get("hcp_id"),
            "recommended_strategy": primary.name,
            "objective": primary.objective,
            "confidence": primary.confidence,
            "key_actions": primary.actions,
            "evidence": evidence,
            "reasoning_chain": primary.reasoning_chain,
        }

    def _competitor_talk_track(self, primary: Strategy) -> list[dict[str, str]]:
        """生成竞品话术。

        Args:
            primary: 首选策略。

        Returns:
            竞品话术列表。
        """
        return [
            {
                "scenario": "竞品新品或新适应症被提及",
                "talk_track": "先确认医生关注点，再用已审批资料说明我方产品适用人群和证据边界。",
            },
            {
                "scenario": "竞品价格或活动压力",
                "talk_track": "回到治疗价值、患者获益和合规服务支持，避免不可验证的价格比较。",
            },
            {
                "scenario": f"当前策略为{primary.name}",
                "talk_track": "围绕本次目标选择一个核心证据点，保留一个后续学术跟进点。",
            },
        ]

    def _objection_handling(self, primary: Strategy) -> list[dict[str, str]]:
        """生成异议处理建议。

        Args:
            primary: 首选策略。

        Returns:
            异议处理列表。
        """
        return [
            {
                "objection": "医生认为已有治疗方案足够稳定",
                "response": "认可现有方案基础，再补充适合特定患者分层的证据与随访支持。",
            },
            {
                "objection": "医生关注竞品证据或患者负担",
                "response": "使用公开、合规、可追溯的材料回应，并记录需医学或市场准入团队支持的问题。",
            },
            {
                "objection": "医生时间有限",
                "response": f"将沟通压缩到{primary.name}的一个关键行动，并约定材料补充时间。",
            },
        ]

    def _follow_up_strategy(self, primary: Strategy) -> dict[str, Any]:
        """生成跟进策略。

        Args:
            primary: 首选策略。

        Returns:
            跟进策略字典。
        """
        return {
            "next_step": primary.actions[-1],
            "timeline": "3-7天内完成材料补充或学术资源匹配",
            "success_signal": "HCP确认下一次沟通主题或接受材料/会议邀请",
            "compliance_note": "所有跟进动作需留痕，并使用已审批内容。",
        }

    def _render_text(self, payload: dict[str, Any]) -> str:
        """渲染自然语言 Brief。

        Args:
            payload: 结构化 Brief 负载。

        Returns:
            自然语言文本。
        """
        brief = payload["pre_call_brief"]
        actions = "；".join(brief["key_actions"])
        objections = "；".join(item["response"] for item in payload["objection_handling"])
        follow_up = payload["follow_up_strategy"]
        return (
            f"Pre-call Brief：本次建议采用「{brief['recommended_strategy']}」策略，"
            f"目标是{brief['objective']} 置信度 {brief['confidence']:.2f}。\n"
            f"关键行动：{actions}。\n"
            f"竞品话术：先确认关注点，使用已审批资料说明证据边界，避免不可验证比较。\n"
            f"异议处理：{objections}。\n"
            f"跟进策略：{follow_up['timeline']}，成功信号为{follow_up['success_signal']}。"
        )
