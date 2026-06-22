"""Sales Suggestion L4 trigger — 拜访完成后多步信息收集→因果推断→策略推荐。"""

import logging

from cloud.app.agent_runtime.core.runtime_core import RuntimeCore
from cloud.app.agent_runtime.core.trigger import run_agent_trigger

logger = logging.getLogger(__name__)

AGENT_KEY = "sales_suggestion"
GOAL = "生成拜访后销售策略建议"


def build_suggestion_plan(visit_event: dict) -> list[dict]:
    """构建销售建议生成计划。

    多步信息收集：
    1. 查询HCP画像
    2. 查询历史拜访记录
    3. 查询竞品动态
    4. 因果推断分析
    5. 输出Pre-call Brief + 策略推荐
    """
    hcp_id = visit_event.get("hcp_id", "")
    rep_id = visit_event.get("rep_id", "")
    return [
        {
            "step": 1,
            "action": "query_hcp_profile",
            "description": "查询HCP画像",
            "params": {"hcp_id": hcp_id},
        },
        {
            "step": 2,
            "action": "query_visit_history",
            "description": "查询历史拜访记录",
            "params": {"hcp_id": hcp_id, "rep_id": rep_id, "limit": 10},
        },
        {
            "step": 3,
            "action": "query_competitor_intel",
            "description": "查询竞品动态",
            "params": {"hcp_id": hcp_id},
        },
        {
            "step": 4,
            "action": "run_causal_attribution",
            "description": "因果推断分析——预测不同策略的HCP接受概率",
            "params": {
                "hcp_id": hcp_id,
                "rep_id": rep_id,
                "visit_context": visit_event.get("context", {}),
            },
        },
        {
            "step": 5,
            "action": "generate_brief",
            "description": "输出结构化销售建议：Pre-call Brief + 竞品话术 + 跟进策略",
            "params": {
                "strategy_count": 3,
                "include_competitive_talk_track": True,
            },
        },
    ]


def suggestion_monitor_trigger(runtime: RuntimeCore, visit_event: dict) -> dict:
    """suggestion monitor trigger. 拜访完成后生成多方案策略建议。"""
    plan = build_suggestion_plan(visit_event)
    return run_agent_trigger(runtime, AGENT_KEY, GOAL, visit_event, {"_plan": plan})
