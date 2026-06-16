"""Compliance Monitor L4 trigger — thin wrapper around the generic trigger."""

import logging

from cloud.app.agent_runtime.runtime_core import RuntimeCore
from cloud.app.agent_runtime.trigger import run_agent_trigger

logger = logging.getLogger(__name__)

AGENT_KEY = "compliance_monitor"
GOAL = "合规检查"


def build_compliance_plan(task: str, context: dict | None = None) -> list[dict]:
    """构建合规调查计划。

    Steps: check expenses → check visits → trace distribution → cross-validate → conclude.
    """
    ctx = context or {}
    return [
        {
            "step": 1,
            "action": "verify_expense",
            "description": "核查费用数据",
            "params": {"rep_id": ctx.get("rep_id"), "expense_data": ctx.get("expense_data")},
        },
        {
            "step": 2,
            "action": "verify_visit",
            "description": "核查拜访数据",
            "params": {"rep_id": ctx.get("rep_id"), "visit_data": ctx.get("visit_data")},
        },
        {
            "step": 3,
            "action": "trace_distribution",
            "description": "追踪流向数据",
            "params": {"rep_id": ctx.get("rep_id"), "distribution_data": ctx.get("distribution_data")},
        },
        {
            "step": 4,
            "action": "triangulation_check",
            "description": "三角勾稽交叉验证",
            "params": {
                "rep_id": ctx.get("rep_id"),
                "expense_data": ctx.get("expense_data"),
                "visit_data": ctx.get("visit_data"),
                "distribution_data": ctx.get("distribution_data"),
            },
        },
        {
            "step": 5,
            "action": "complete",
            "description": "输出合规判定结论",
            "params": {},
        },
    ]


def compliance_monitor_trigger(
    runtime: RuntimeCore,
    task: str,
    context: dict | None = None,
) -> dict:
    """compliance monitor trigger."""
    plan = build_compliance_plan(task, context)
    return run_agent_trigger(runtime, AGENT_KEY, task, context, {"_plan": plan})
