"""Compliance Monitor L4 trigger — routes compliance events through agent_runtime.execute()."""

import logging
import time
import uuid

from cloud.app.agent_runtime.agent_specs import AGENT_SPECS
from cloud.app.agent_runtime.runtime_core import RuntimeCore

logger = logging.getLogger(__name__)


def build_compliance_plan(task: str, context: dict | None = None) -> list[dict]:
    """Build a structured compliance investigation plan.
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
    """Trigger compliance_monitor via the L4 agent_runtime.execute() loop.
    Instead of calling tool functions directly, this goes through planner→executor→verifier→analyzer→reflector.
    """
    agent_key = "compliance_monitor"
    spec = AGENT_SPECS.get(agent_key)
    if not spec:
        return {"status": "error", "result": f"unknown agent: {agent_key}"}

    plan = build_compliance_plan(task, context)
    enriched_context = {
        **(context or {}),
        "_plan": plan,
        "_trigger_source": "compliance_monitor_trigger",
        "_trace_id": str(uuid.uuid4()),
    }

    start = time.time()
    result = runtime.execute(task, agent_key, enriched_context)
    elapsed = time.time() - start

    logger.info(
        "Compliance L4 trigger: agent=%s status=%s iterations=%d tool_calls=%d elapsed=%.2fs",
        agent_key, result.status, result.iterations, result.tool_calls, elapsed,
    )

    return {
        "status": result.status,
        "result": result.result,
        "iterations": result.iterations,
        "tool_calls": result.tool_calls,
        "logs": result.logs,
        "elapsed_seconds": round(elapsed, 3),
        "metadata": result.metadata,
    }
