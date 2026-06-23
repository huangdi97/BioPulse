"""Compliance Monitor L4 trigger — 全息校验交叉验证，异常时触发红灯事件。"""

import logging

from cloud.app.agent_runtime.core.runtime_core import RuntimeCore
from cloud.app.agent_runtime.core.trigger import run_agent_trigger
from cloud.app.models.red_flag_event import RedFlagEvent, RedFlagSeverity

logger = logging.getLogger(__name__)

AGENT_KEY = "compliance_monitor"
GOAL = "合规检查"


def _infer_severity(holographic_result: dict) -> RedFlagSeverity:
    """根据全息校验结果推断严重级别。"""
    severity_map = {
        "窜货": RedFlagSeverity.critical,
        "造假": RedFlagSeverity.critical,
        "严重违规": RedFlagSeverity.critical,
        "费用浪费": RedFlagSeverity.high,
        "拜访造假": RedFlagSeverity.high,
        "虚假活动": RedFlagSeverity.high,
        "管理失职": RedFlagSeverity.medium,
        "规则僵化": RedFlagSeverity.low,
    }
    pattern = holographic_result.get("detected_pattern", "")
    for key, sev in severity_map.items():
        if key in pattern:
            return sev
    return RedFlagSeverity.medium


def build_compliance_plan(task: str, context: dict | None = None) -> list[dict]:
    """构建合规调查计划。

    Steps 1-4: 数据收集与交叉验证
    Step 5: 输出结构化 RedFlagEvent（如有异常）
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
            "action": "holographic_audit_check",
            "description": "全息校验交叉验证",
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
            "description": "输出合规判定结论，如有异常生成红灯事件",
            "params": {},
        },
    ]


def compliance_monitor_trigger(
    runtime: RuntimeCore,
    task: str,
    context: dict | None = None,
) -> dict:
    """Compliance monitor trigger. 执行合规调查计划，输出 RedFlagEvent（如有异常）。"""
    plan = build_compliance_plan(task, context)
    result = run_agent_trigger(runtime, AGENT_KEY, task, context, {"_plan": plan})

    # 如果执行成功且有步骤输出，检查是否需要生成红灯事件
    if result.get("status") in ("completed", "success"):
        step_results = result.get("metadata", {}).get("step_results", {})
        holographic_result = step_results.get("step_4", {})
        anomaly_detected = holographic_result.get("anomaly_detected", False)

        if anomaly_detected:
            event = RedFlagEvent.create(
                severity=_infer_severity(holographic_result),
                rep_id=(context or {}).get("rep_id", ""),
                region=(context or {}).get("region", ""),
                description=holographic_result.get("summary", "合规异常"),
                evidence_chain=[
                    step_results.get("step_1", {}).get("result", ""),
                    step_results.get("step_2", {}).get("result", ""),
                    step_results.get("step_3", {}).get("result", ""),
                ],
            )
            result["red_flag"] = event.to_dict()
            logger.info(
                "红灯事件触发: id=%s severity=%s rep=%s",
                event.red_flag_id,
                event.severity,
                event.rep_id,
            )

    return result
