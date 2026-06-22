"""Analysis L4 trigger — 订阅合规红灯事件，执行假设→验证→收敛→叙事完整循环。"""

import logging

from cloud.app.agent_runtime.core.analysis_agent import AnalysisAgent
from cloud.app.agent_runtime.core.runtime_core import RuntimeCore
from cloud.app.agent_runtime.core.trigger import run_agent_trigger
from cloud.app.agent_runtime.safety.cost_governor import CostGovernor

logger = logging.getLogger(__name__)

AGENT_KEY = "anomaly_analysis"
GOAL = "分析红灯事件"


def build_analysis_plan(red_light_event: dict) -> list[dict]:
    """构建异常分析计划。

    1. 收集关联数据
    2. 模式分析
    3. 因果推断
    4. 生成叙事报告
    """
    return [
        {
            "step": 1,
            "action": "collect_related_data",
            "description": "收集与红灯事件关联的费用/拜访/经销商数据",
            "params": {
                "rep_id": red_light_event.get("rep_id", ""),
                "red_flag_id": red_light_event.get("red_flag_id", ""),
                "time_range_days": 90,
            },
        },
        {
            "step": 2,
            "action": "run_pattern_analysis",
            "description": "运行模式分析，搜索其他代表是否有相似模式",
            "params": {
                "rep_id": red_light_event.get("rep_id", ""),
                "region": red_light_event.get("region", ""),
            },
        },
        {
            "step": 3,
            "action": "run_causal_inference",
            "description": "因果推断，收敛根因",
            "params": {
                "rep_id": red_light_event.get("rep_id", ""),
                "evidence": red_light_event.get("evidence_chain", []),
            },
        },
        {
            "step": 4,
            "action": "generate_narrative",
            "description": "生成自然语言根因叙事报告",
            "params": {
                "include_recommendation": True,
                "audience": "总裁",
            },
        },
    ]


def analysis_monitor_trigger(runtime: RuntimeCore, red_light_event: dict) -> dict:
    """analysis monitor trigger. 红灯事件→假设→验证→收敛→叙事。

    优先走 AnalysisAgent（HypothesisEngine 管线），回退到 L4 通用执行。
    """
    # 尝试走专用 AnalysisAgent 管线
    try:
        governor = CostGovernor(max_cost=0.50)
        agent = AnalysisAgent(cost_governor=governor)
        result = agent.execute(red_light_event)
        if result.get("status") in ("completed", "budget_exceeded"):
            logger.info(
                "AnalysisAgent 完成: status=%s hypotheses=%d",
                result["status"],
                len(result.get("hypotheses", [])),
            )
            return result
    except Exception as e:
        logger.warning("AnalysisAgent 执行失败，回退到L4通用执行: %s", e)

    # 回退：走通用 L4 trigger
    plan = build_analysis_plan(red_light_event)
    return run_agent_trigger(runtime, AGENT_KEY, GOAL, red_light_event, {"_plan": plan})
